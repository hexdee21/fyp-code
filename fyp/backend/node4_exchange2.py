from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
MINER = "http://127.0.0.1:5000"

@app.route("/new_tx", methods=["POST"])
def new_tx():
    data = request.get_json()
    tx = {
        "sender": "Exchange2",
        "receiver": data.get("receiver","Exchange1"),
        "amount": float(data.get("amount",0.5)),
        "data": data.get("data","P2P trade 0.5 ETH")
    }
    r = requests.post(f"{MINER}/add_tx", json=tx)
    return jsonify({"sent_to_miner": r.json()}), 200

if __name__ == "__main__":
    print("exchange2 running on port 5003")
    app.run(port=5003)
