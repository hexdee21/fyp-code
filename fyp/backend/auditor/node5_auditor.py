from flask import Flask, jsonify, request
import requests
from web3 import Web3
import json
import os
from flask_cors import CORS

from clustering_engine import cluster_wallets
from rules_engine import analyze_transactions   # Optional rule engine

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# ---------------------------------------
# CONFIG
# ---------------------------------------
MINER = "http://127.0.0.1:5000"
BESU_RPC = "http://127.0.0.1:8555"

# ---------------------------------------
# CONNECT TO BESU
# ---------------------------------------
w3 = Web3(Web3.HTTPProvider(BESU_RPC))
if w3.is_connected():
    print("[🔗] Auditor connected to Besu RPC 8555")
else:
    print("[⚠️] Auditor could NOT connect to Besu RPC 8555")

# ---------------------------------------
# LOAD SMART CONTRACT
# ---------------------------------------
contract = None
if os.path.exists("contract_data.json"):
    try:
        with open("contract_data.json", "r") as f:
            data = json.load(f)

        contract_address = Web3.to_checksum_address(data["address"])
        contract_abi = data["abi"]

        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print("[🔗] Smart contract loaded successfully.")
    except Exception as e:
        print(f"[⚠️] Failed to load smart contract: {e}")
        contract = None

else:
    print("[⚠️] contract_data.json missing. On-chain viewing disabled.")

# ---------------------------------------
# ROUTE 1 — OBSERVE BLOCKCHAIN
# ---------------------------------------
@app.route("/observe", methods=["GET"])
def observe():
    try:
        chain = requests.get(f"{MINER}/chain").json()
        return jsonify({
            "audited_blocks": len(chain),
            "latest_block": chain[-1]
        }), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------
# ROUTE 2 — VIEW ON-CHAIN AML LOGS
# ---------------------------------------
@app.route("/view_logs", methods=["GET"])
def view_logs():
    if not contract:
        return jsonify({"error": "Contract not loaded."}), 500

    try:
        # DIRECT CALL TO CONTRACT FUNCTION
        raw_logs = contract.functions.getAllFlaggedTxs().call()

        parsed = []
        for item in raw_logs:
            try:
                parsed.append(json.loads(item))  # decode JSON string stored on-chain
            except:
                parsed.append({"raw": item})

        return jsonify({
            "on_chain_flagged_count": len(parsed),
            "flagged_transactions": parsed
        }), 200

    except Exception as e:
        print("[ERROR] /view_logs:", e)
        return jsonify({"error": str(e)}), 500


# ---------------------------------------
# ROUTE 3 — ANALYZE TRANSACTIONS
# ---------------------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        body = request.get_json()
        if not body or "transactions" not in body:
            return jsonify({"error": "Missing 'transactions' field"}), 400

        txs = body["transactions"]

        flagged = analyze_transactions(txs)
        clusters = cluster_wallets(txs)

        return jsonify({
            "flagged_transactions": flagged,
            "clusters": clusters,
            "total_clusters": len(clusters)
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------
# ROUTE 4 — DIRECT CLUSTER ENDPOINT
# ---------------------------------------
@app.route("/cluster", methods=["POST"])
def cluster_endpoint():
    try:
        body = request.get_json()
        if not body or "transactions" not in body:
            return jsonify({"error": "Missing 'transactions' field"}), 400

        clusters = cluster_wallets(body["transactions"])

        return jsonify({
            "total_clusters": len(clusters),
            "clusters": clusters
        }), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------
# MAIN
# ---------------------------------------
if __name__ == "__main__":
    print("Auditor running on port 5004 (Clustering + On-Chain Viewer)")
    app.run(port=5004, host="0.0.0.0")
