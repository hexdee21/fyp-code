from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
MINER = "http://127.0.0.1:5000"

@app.route("/new_tx", methods=["POST"])
def new_tx():
    data = request.get_json()
    tx = {
        "sender": "Exchange1",
        "receiver": data.get("receiver","Exchange2"),
        "amount": float(data.get("amount",0.5)),  # e.g., 0.5 ETH
        "data": data.get("data","Customer withdrawal 0.5 ETH")
    }
    r = requests.post(f"{MINER}/add_tx", json=tx)
    return jsonify({"sent_to_miner": r.json()}), 200

if __name__ == "__main__":
    print("exchange1 running on port 5002")
    app.run(port=5002)
