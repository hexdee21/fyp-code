from web3 import Web3
from solcx import compile_standard, install_solc, set_solc_version
import json, os

# --- Connect to your local Besu blockchain ---
w3 = Web3(Web3.HTTPProvider("http://127.0.0.1:8555"))
print("Connected to Besu:", w3.is_connected())

# --- Replace this with your Besu private key ---
PRIVATE_KEY = "0x18801b12f46b46e6e12e6116af454dc2432235101f51f243c974730985e057cd"
acct = w3.eth.account.from_key(PRIVATE_KEY)
print("Using account:", acct.address)

# --- Read your Solidity contract ---
with open("FlaggedLogStorage.sol", "r") as file:
    contract_source = file.read()

# --- Install and select Solidity compiler version ---
install_solc("0.8.0")
set_solc_version("0.8.0")

# --- Compile contract ---
compiled_sol = compile_standard({
    "language": "Solidity",
    "sources": {"FlaggedLogStorage.sol": {"content": contract_source}},
    "settings": {
        "outputSelection": {
            "*": {"*": ["abi", "evm.bytecode"]}
        }
    }
})

# --- Extract bytecode and ABI ---
bytecode = compiled_sol["contracts"]["FlaggedLogStorage.sol"]["FlaggedLogStorage"]["evm"]["bytecode"]["object"]
abi = compiled_sol["contracts"]["FlaggedLogStorage.sol"]["FlaggedLogStorage"]["abi"]

# --- Deploy contract ---
contract = w3.eth.contract(abi=abi, bytecode=bytecode)
nonce = w3.eth.get_transaction_count(acct.address)

transaction = contract.constructor().build_transaction({
    "from": acct.address,
    "nonce": nonce,
    "gas": 2000000,
    "gasPrice": w3.to_wei("1", "gwei")
})

# --- Sign and send transaction ---
signed_tx = w3.eth.account.sign_transaction(transaction, PRIVATE_KEY)
tx_hash = w3.eth.send_raw_transaction(signed_tx.raw_transaction)
print("⏳ Deploying contract...")

tx_receipt = w3.eth.wait_for_transaction_receipt(tx_hash)
print("✅ Contract deployed at:", tx_receipt.contractAddress)

# --- Save ABI and address ---
with open("contract_data.json", "w") as f:
    json.dump({"address": tx_receipt.contractAddress, "abi": abi}, f, indent=4)

print("💾 Contract ABI and address saved to contract_data.json")
