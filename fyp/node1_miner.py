from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from blockchain import Blockchain
from rules_engine import RuleEngine
from web3 import Web3
import json, time, os

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# --- Initialize Blockchain and Rule Engine ---
chain = Blockchain()
rules = RuleEngine("rules.json")

# --- Connect to Besu blockchain ---
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8555"))
if w3.is_connected():
    print("[🔗] Connected to Besu blockchain")
else:
    print("[⚠️] Could not connect to Besu. Check if it's running on port 8555.")

# --- Load deployed contract info ---
with open("contract_data.json", "r") as f:
    contract_info = json.load(f)

contract_address = Web3.to_checksum_address(contract_info["address"])
contract_abi = contract_info["abi"]
contract = w3.eth.contract(address=contract_address, abi=contract_abi)

# --- Miner private key and account ---
PRIVATE_KEY = "0x18801b12f46b46e6e12e6116af454dc2432235101f51f243c974730985e057cd"
ACCOUNT = w3.eth.account.from_key(PRIVATE_KEY)

# ---------------------- ROUTES ----------------------

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

    # Step 3: If flagged, log locally + send to Besu
    if flagged:
        alert = {
            "tx": tx,
            "matched_rules": [r["name"] for r in matched_rules],
            "risk_levels": [r["risk_level"] for r in matched_rules],
            "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
        }

        # Save locally in flagged_log.json
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

        # --- Send flagged transaction to Besu blockchain ---
        try:
            # Convert alert to JSON string for on-chain storage
            flagged_json = json.dumps({
                "sender": tx.get("sender"),
                "receiver": tx.get("receiver"),
                "amount": tx.get("amount"),
                "rules_triggered": [r["name"] for r in matched_rules],
                "risk_levels": [r["risk_level"] for r in matched_rules],
                "timestamp": alert["timestamp"]
            })

            nonce = w3.eth.get_transaction_count(ACCOUNT.address)

            txn = contract.functions.storeFlaggedTx(flagged_json).build_transaction({
                'from': ACCOUNT.address,
                'nonce': nonce,
                'gas': 2000000,
                'gasPrice': w3.to_wei('1', 'gwei')
            })

            signed_tx = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
            tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
            print(f"[🧱 ON-CHAIN] Sending flagged transaction to blockchain...")

            tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
            print(f"[✅ STORED] Flagged transaction stored on-chain. TxHash: {tx_receipt.transactionHash.hex()}")

        except Exception as e:
            print(f"[❌ ERROR] Failed to store transaction on blockchain: {e}")

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


# ---------------------- MAIN ----------------------
if __name__ == "__main__":
    print("Miner running on port 5000 (Monitoring Mode + On-Chain Logging)")
    socketio.run(app, port=5000)
