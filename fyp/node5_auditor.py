from flask import Flask, jsonify
import requests

app = Flask(__name__)
MINER = "http://127.0.0.1:5000"

@app.route("/observe", methods=["GET"])
def observe():
    chain = requests.get(f"{MINER}/chain").json()
    return jsonify({"audited_blocks": len(chain), "latest": chain[-1]}), 200

if __name__ == "__main__":
    print("auditor running on port 5004")
    app.run(port=5004)
