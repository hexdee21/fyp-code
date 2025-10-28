from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from blockchain import Blockchain
from rules_engine import RuleEngine
import json, time, os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# Initialize Blockchain and Rule Engine
chain = Blockchain()
rules = RuleEngine("rules.json")

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(chain.chain), 200

@app.route("/mine", methods=["GET"])
def mine():
    prev_hash = chain.last_block()["hash"]
    new_block = chain.create_block(prev_hash)
    socketio.emit("new_block", new_block)
    print(f"[MINER] Block #{new_block['index']} mined.")
    return jsonify(new_block), 200

@app.route("/add_tx", methods=["POST"])
def add_tx():
    tx = request.get_json()

    # Step 1: Evaluate rules
    flagged, matched_rules = rules.evaluate(tx)

    # Step 2: Always add to blockchain (monitoring mode)
    idx = chain.add_transaction(
        tx.get("sender"),
        tx.get("receiver"),
        tx.get("amount"),
        tx.get("data", "")
    )

    # Step 3: If flagged, log evidence
    if flagged:
        alert = {
            "tx": tx,
            "matched_rules": [r["name"] for r in matched_rules],
            "risk_levels": [r["risk_level"] for r in matched_rules],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        if not os.path.exists("flagged_log.json"):
            with open("flagged_log.json", "w") as f:
                json.dump([alert], f, indent=4)
        else:
            with open("flagged_log.json", "r+") as f:
                try:
                    data = json.load(f)
                except json.JSONDecodeError:
                    data = []
                data.append(alert)
                f.seek(0)
                json.dump(data, f, indent=4)

        print(f"[⚠️ ALERT] Suspicious Transaction Flagged:")
        print(f"→ Sender: {tx.get('sender')}, Receiver: {tx.get('receiver')}, Amount: {tx.get('amount')}")
        print(f"→ Triggered Rules: {[r['name'] for r in matched_rules]}")

        return jsonify({
            "status": "flagged",
            "block_index": idx,
            "triggered_rules": [r["name"] for r in matched_rules]
        }), 200

    # Step 4: If clean
    print(f"[✅ ACCEPTED] Clean transaction from {tx.get('sender')} to {tx.get('receiver')} amount {tx.get('amount')}")
    return jsonify({"status": "clean", "block_index": idx}), 201

@socketio.on("new_block")
def sync_block(block):
    chain.chain.append(block)

if __name__ == "__main__":
    print("Miner running on port 5000 (Monitoring Mode)")
    socketio.run(app, port=5000)
