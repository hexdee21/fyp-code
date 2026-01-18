from flask import Flask, request, jsonify
import requests

app = Flask(__name__)
MINER = "http://127.0.0.1:5000"

@app.route("/new_tx", methods=["POST"])
def new_tx():
    data = request.get_json()
    tx = {
        "sender": "FIA-Regulator",
        "receiver": data.get("receiver","Exchange1"),
        "amount": 0,
        "data": data.get("data","AML alert – suspicious wallet 0xABC")
    }
    r = requests.post(f"{MINER}/add_tx", json=tx)
    return jsonify({"sent_to_miner": r.json()}), 200

if __name__ == "__main__":
    print("regulator running on port 5001")
    app.run(port=5001)
