from flask import Flask, jsonify
import requests
from web3 import Web3
import json, os

app = Flask(__name__)

MINER = "http://127.0.0.1:5000"
BESU_RPC = "http://127.0.0.1:8555"

# --- Connect to Besu blockchain ---
w3 = Web3(Web3.HTTPProvider(BESU_RPC))
if w3.is_connected():
    print("[🔗] Connected to Besu blockchain (Auditor)")
else:
    print("[⚠️] Could not connect to Besu blockchain. Check port 8555.")

# --- Load contract data ---
if os.path.exists("contract_data.json"):
    with open("contract_data.json", "r") as f:
        contract_data = json.load(f)
    contract_address = Web3.to_checksum_address(contract_data["address"])
    contract_abi = contract_data["abi"]
    contract = w3.eth.contract(address=contract_address, abi=contract_abi)
else:
    contract = None
    print("[⚠️] contract_data.json not found. On-chain log viewing disabled.")


@app.route("/observe", methods=["GET"])
def observe():
    """View blockchain summary (local Flask chain)."""
    chain = requests.get(f"{MINER}/chain").json()
    return jsonify({"audited_blocks": len(chain), "latest": chain[-1]}), 200


@app.route("/view_logs", methods=["GET"])
def view_logs():
    """View flagged transactions directly from Besu smart contract."""
    if not contract:
        return jsonify({"error": "Contract not loaded."}), 500

    try:
        # Call the smart contract function to get all flagged txs
        flagged_logs = contract.functions.getAllFlaggedTxs().call()

        # Each entry is stored as JSON string — convert back to dict
        parsed_logs = []
        for entry in flagged_logs:
            try:
                parsed_logs.append(json.loads(entry))
            except Exception:
                parsed_logs.append({"raw": entry})

        return jsonify({
            "on_chain_flagged_count": len(parsed_logs),
            "flagged_transactions": parsed_logs
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


if __name__ == "__main__":
    print("Auditor running on port 5004 (Now with On-Chain Log Viewer)")
    app.run(port=5004, host="0.0.0.0")
