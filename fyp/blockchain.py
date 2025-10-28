import json, time, hashlib

class Blockchain:
    def __init__(self):
        self.chain = []
        self.pending_tx = []
        self.create_block(previous_hash="GENESIS")

    def create_block(self, previous_hash):
        block = {
            "index": len(self.chain) + 1,
            "timestamp": time.time(),
            "transactions": self.pending_tx,
            "previous_hash": previous_hash,
            "hash": ""
        }
        block["hash"] = self.hash(block)
        self.pending_tx = []
        self.chain.append(block)
        return block

    def add_transaction(self, sender, receiver, amount, data):
        tx = {
            "sender": sender,
            "receiver": receiver,
            "amount": amount,
            "data": data,
            "timestamp": time.time()
        }
        self.pending_tx.append(tx)
        return len(self.chain) + 1

    @staticmethod
    def hash(block):
        return hashlib.sha256(json.dumps(block, sort_keys=True).encode()).hexdigest()

    def last_block(self):
        return self.chain[-1]
