# node1_miner.py
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from flask import Flask, jsonify, request
from flask_socketio import SocketIO
from flask_cors import CORS
from web3 import Web3
import json, time, os, sqlite3
from datetime import datetime, timedelta

# ✅ Local imports (after restructuring)
from backend.miner.blockchain import Blockchain
from backend.auditor.rules_engine import RuleEngine

# ---------- CONFIG ----------
DB_PATH = "tx_history.db"
CLEAN_MINE_THRESHOLD = 3   # auto-mine after this many clean TXs
PRIVATE_KEY = "0x18801b12f46b46e6e12e6116af454dc2432235101f51f243c974730985e057cd"
CONTRACT_INFO_PATH = "contract_data.json"
BESU_RPC = "http://127.0.0.1:8555"

# ---------- MySQL config for wallets (same as auth)
MYSQL_CONFIG = {
    "host": "127.0.0.1",
    "user": "admin",
    "password": "admin123",
    "database": "aml_system"
}

# ---------- DB INIT ----------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS transactions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        data TEXT,
        timestamp REAL,
        path TEXT,
        device_type TEXT,
        country TEXT,
        merchant_category TEXT,
        payment_method TEXT,
        customer_id TEXT
    )
    ''')
    # links table: lightweight edge log used for chain/link detection
    c.execute('''
    CREATE TABLE IF NOT EXISTS links (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        sender TEXT,
        receiver TEXT,
        amount REAL,
        timestamp REAL
    )
    ''')
    conn.commit()
    conn.close()

init_db()

def save_tx_to_db(tx):
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    ts = float(tx.get("timestamps")[-1]) if tx.get("timestamps") else time.time()
    c.execute('''
    INSERT INTO transactions
      (sender, receiver, amount, data, timestamp, path, device_type, country, merchant_category, payment_method, customer_id)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    ''', (
        tx.get("sender"),
        tx.get("receiver"),
        float(tx.get("amount") or 0),
        json.dumps(tx.get("data")) if isinstance(tx.get("data"), (dict, list)) else tx.get("data"),
        ts,
        json.dumps(tx.get("path")) if tx.get("path") else json.dumps([]),
        tx.get("device_type"),
        tx.get("country"),
        tx.get("merchant_category"),
        tx.get("payment_method"),
        tx.get("customer_id")
    ))
    # also insert to links table (edge record)
    try:
        c.execute('''
        INSERT INTO links (sender, receiver, amount, timestamp)
        VALUES (?, ?, ?, ?)
        ''', (tx.get("sender"), tx.get("receiver"), float(tx.get("amount") or 0), ts))
    except Exception as e:
        print("[⚠️] Could not write links table:", e)
    conn.commit()
    conn.close()

def trace_full_transaction_path(tx, conn, now_ts):
    """
    Trace the complete transaction path by following previous hops within time limits.
    Returns enhanced transaction data with full path information for Rule 3.
    """
    MAX_HOP_TIME = 120  # 2 minutes between consecutive hops
    c = conn.cursor()
    
    # Initialize path with current transaction
    full_path = [tx.get("sender"), tx.get("receiver")]
    timestamps = [now_ts]
    amounts = [float(tx.get("amount", 0))]
    visited = set(full_path)
    
    def find_previous_hop(current_sender, current_time):
        """
        Find if any previous transaction sent to current_sender exists
        within MAX_HOP_TIME window.
        """
        c.execute('''
            SELECT sender, receiver, timestamp, amount
            FROM transactions
            WHERE receiver = ? AND timestamp <= ?
            ORDER BY timestamp DESC
            LIMIT 10
        ''', (current_sender, current_time))
        rows = c.fetchall() or []
        
        for prev_sender, prev_receiver, prev_ts, prev_amount in rows:
            if prev_sender in visited:
                continue
            # Time proximity check
            time_gap = abs(current_time - prev_ts)
            if time_gap <= MAX_HOP_TIME:
                return (prev_sender, prev_ts, float(prev_amount))
        return None
    
    # Trace backwards from sender
    current = tx.get("sender")
    current_time = now_ts
    
    while True:
        hop_data = find_previous_hop(current, current_time)
        if not hop_data:
            break
        prev_sender, prev_ts, prev_amount = hop_data
        
        # Add to beginning of path
        full_path.insert(0, prev_sender)
        timestamps.insert(0, prev_ts)
        amounts.insert(0, prev_amount)
        visited.add(prev_sender)
        
        # Move to previous hop
        current = prev_sender
        current_time = prev_ts
    
    # Calculate metrics for Rule 3
    num_accounts = len(full_path)
    num_layers = max(0, num_accounts - 1)
    total_amount = sum(amounts)
    
    # Calculate average delay between layers
    if len(timestamps) > 1:
        time_deltas = []
        for i in range(1, len(timestamps)):
            delta = abs(timestamps[i] - timestamps[i-1])
            time_deltas.append(delta)
        avg_delay = sum(time_deltas) / len(time_deltas) if time_deltas else float('inf')
    else:
        avg_delay = float('inf')
    
    return {
        'full_path': full_path,
        'path_timestamps': timestamps,
        'path_amounts': amounts,
        'num_accounts_involved': num_accounts,
        'num_layers': num_layers,
        'total_amount': total_amount,
        'avg_delay_between_layers': avg_delay
    }


# ---------- METRICS ENRICHMENT ----------
def compute_metrics(tx):
    """
    Compute derived fields required by rules.json and later reporting.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now_ts = float(tx.get("timestamps")[-1]) if tx.get("timestamps") else time.time()
    one_hour_ago = now_ts - 3600
    one_day_ago = now_ts - 24 * 3600
    seven_days_ago = now_ts - 7 * 86400
    three_days_ago = now_ts - 3 * 86400

    # === ENHANCED PATH TRACING FOR RULE 3 ===
    # This populates the metrics that rules.json will evaluate
    path_data = trace_full_transaction_path(tx, conn, now_ts)
    
    # Update transaction with traced path data
    tx["path"] = path_data['full_path']
    tx["timestamps"] = path_data['path_timestamps']
    tx["num_layers"] = path_data['num_layers']
    tx["num_accounts_involved"] = path_data['num_accounts_involved']
    tx["total_amount"] = path_data['total_amount']
    tx["avg_delay_between_layers"] = path_data['avg_delay_between_layers']
    
    # Set time constant used by Rule 3
    tx["48_hours"] = 48 * 3600  # Used in: avg_delay_between_layers < 48_hours
    
    # Debug output (optional - remove in production)
    print("\n[🔗 Path Tracing - Metrics for Rules Engine]")
    print(f"  Full Path: {' → '.join(tx['path'])}")
    print(f"  num_accounts_involved: {tx['num_accounts_involved']} (Rule 3 needs > 3)")
    print(f"  total_amount: ${tx['total_amount']:,.2f} (Rule 3 needs > 50000)")
    print(f"  avg_delay_between_layers: {tx['avg_delay_between_layers']:.2f}s (Rule 3 needs < 172800s)")

    # === Continue with other metrics (keep existing code) ===
    
    # --- 5️⃣ Receiver stats (7 days) ---
    c.execute('''SELECT COUNT(*), COALESCE(SUM(amount),0)
                 FROM transactions WHERE receiver=? AND timestamp>=?''',
                 (tx.get("receiver"), seven_days_ago))
    row = c.fetchone() or (0, 0)
    tx["count_to_same_receiver_7d"], tx["total_to_same_receiver_7d"] = int(row[0]), float(row[1])

    # --- 6️⃣ Distinct countries ---
    c.execute('''SELECT COUNT(DISTINCT country)
                 FROM transactions WHERE sender=? AND timestamp>=? AND country IS NOT NULL''',
                 (tx.get("sender"), seven_days_ago))
    tx["num_countries_involved_7d"] = int(c.fetchone()[0] or 0)

    # --- 7️⃣ Sender high frequency (1h) ---
    c.execute('''SELECT COUNT(*) FROM transactions WHERE sender=? AND timestamp>=?''',
              (tx.get("sender"), one_hour_ago))
    tx["num_transactions_1h"] = int(c.fetchone()[0] or 0)

    # --- 8️⃣ Unique devices (3d) ---
    c.execute('''SELECT COUNT(DISTINCT device_type)
                 FROM transactions WHERE sender=? AND timestamp>=? AND device_type IS NOT NULL''',
              (tx.get("sender"), three_days_ago))
    tx["unique_device_count_3d"] = int(c.fetchone()[0] or 0)

    # --- 9️⃣ Previous STRs count ---
    previous_STRs = 0
    if os.path.exists("flagged_log.json"):
        try:
            with open("flagged_log.json") as f:
                arr = json.load(f)
                previous_STRs = sum(1 for a in arr if a.get("tx", {}).get("sender") == tx.get("sender"))
        except Exception:
            previous_STRs = 0
    tx["previous_STRs"] = previous_STRs

    # --- 🔟 Dispersion (1h) ---
    c.execute('''SELECT COUNT(DISTINCT receiver), COALESCE(SUM(amount),0)
                 FROM transactions WHERE sender=? AND timestamp>=?''',
              (tx.get("sender"), one_hour_ago))
    row = c.fetchone() or (0, 0)
    tx["sender_out_degree"] = int(row[0])
    tx["total_outgoing_value_1h"] = float(row[1])

    # --- 11️⃣ Aggregation (1h) ---
    c.execute('''SELECT COUNT(DISTINCT sender), COALESCE(SUM(amount),0)
                 FROM transactions WHERE receiver=? AND timestamp>=?''',
              (tx.get("receiver"), one_hour_ago))
    row = c.fetchone() or (0, 0)
    tx["receiver_in_degree"] = int(row[0])
    tx["total_incoming_value_1h"] = float(row[1])

    # --- 12️⃣ Common Receiver (1h) ---
    c.execute('''SELECT COUNT(DISTINCT sender), COALESCE(SUM(amount),0)
                 FROM transactions WHERE receiver=? AND timestamp>=?''',
              (tx.get("receiver"), one_hour_ago))
    row = c.fetchone() or (0, 0)
    tx["num_unique_senders_to_receiver_1h"] = int(row[0])
    tx["receiver_total_1h"] = float(row[1])

    # --- 13️⃣ 24-hour metrics ---
    c.execute('''SELECT COUNT(DISTINCT receiver), COALESCE(SUM(amount),0)
                 FROM transactions WHERE sender=? AND timestamp>=?''', (tx.get("sender"), one_day_ago))
    row = c.fetchone() or (0, 0)
    tx["sender_out_degree_24h"] = int(row[0])
    tx["total_outgoing_value_24h"] = float(row[1])

    c.execute('''SELECT COUNT(DISTINCT sender), COALESCE(SUM(amount),0)
                 FROM transactions WHERE receiver=? AND timestamp>=?''', (tx.get("receiver"), one_day_ago))
    row = c.fetchone() or (0, 0)
    tx["receiver_in_degree_24h"] = int(row[0])
    tx["total_incoming_value_24h"] = float(row[1])

    # --- 14️⃣ Multi-hop detection (for other rules) ---
    hop_chain = [tx.get("sender"), tx.get("receiver")]
    visited_hops = set(hop_chain)

    def find_previous_hop_simple(current_sender):
        c.execute('''
            SELECT sender, timestamp
            FROM transactions
            WHERE receiver = ?
            ORDER BY timestamp DESC
            LIMIT 5
        ''', (current_sender,))
        rows = c.fetchall() or []

        for prev_sender, prev_ts in rows:
            if prev_sender in visited_hops:
                continue
            if abs(now_ts - prev_ts) <= 120:  # 2 minutes
                return prev_sender
        return None

    current = tx.get("sender")
    while True:
        prev_sender = find_previous_hop_simple(current)
        if not prev_sender:
            break
        hop_chain.insert(0, prev_sender)
        visited_hops.add(prev_sender)
        current = prev_sender

    tx["hop_chain"] = hop_chain
    tx["hop_count"] = max(0, len(hop_chain) - 1)
    tx["is_multi_hop"] = tx["hop_count"] >= 2

    # --- 15️⃣ Linked-chain detection (Rule 35) ---
    tx["is_linked_chain"] = False
    tx["linked_chain_common_receiver"] = None
    tx["linked_chain_members"] = []

    try:
        def detect_for_origin(origin):
            c.execute('''SELECT DISTINCT receiver FROM links WHERE sender=? AND timestamp>=?''', (origin, one_day_ago))
            first_hops = [r[0] for r in c.fetchall()] or []
            if len(first_hops) < 3:
                return (None, None)

            final_map = {}
            for fh in first_hops:
                c.execute('''SELECT receiver, COALESCE(SUM(amount),0)
                             FROM links WHERE sender=? AND timestamp>=? GROUP BY receiver''', (fh, one_day_ago))
                for fr, amt in c.fetchall() or []:
                    final_map.setdefault(fr, []).append((fh, float(amt)))

            for fr, senders_list in final_map.items():
                unique_senders = set(s for s, _ in senders_list)
                if len(unique_senders) >= 3:
                    amounts = [a for _, a in senders_list]
                    if len(amounts) > 1:
                        avg = sum(amounts) / len(amounts)
                        max_dev = max(abs(a - avg) for a in amounts)
                        if max_dev <= max(0.3 * avg, 10000):
                            members = set([origin, fr] + [s for s, _ in senders_list] + first_hops)
                            return (fr, list(members))
                    else:
                        members = set([origin, fr] + [s for s, _ in senders_list] + first_hops)
                        return (fr, list(members))
            return (None, None)

        common_receiver, members = detect_for_origin(tx.get("sender"))
        if not common_receiver:
            c.execute('''SELECT DISTINCT sender FROM links WHERE receiver=? AND timestamp>=?''', (tx.get("sender"), one_day_ago))
            upstream_origins = [r[0] for r in c.fetchall()] or []
            for origin in upstream_origins:
                common_receiver, members = detect_for_origin(origin)
                if common_receiver:
                    break

        if common_receiver:
            tx["is_linked_chain"] = True
            tx["linked_chain_common_receiver"] = common_receiver
            tx["linked_chain_members"] = members

    except Exception as e:
        print("[⚠️] Linked-chain detection error:", e)

    # --- 16️⃣ Time constants ---
    tx["2_days"] = 2 * 86400
    tx["1_hour"] = 3600

    conn.close()
# ---------- APP + INIT ----------
app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

chain = Blockchain()
rules_path = os.path.join(os.path.dirname(__file__), "../auditor/rules.json")
rules = RuleEngine(os.path.abspath(rules_path))

# Connect to Besu
w3 = Web3(Web3.HTTPProvider(BESU_RPC))
if w3.is_connected():
    print("[🔗] Connected to Besu blockchain")
else:
    print("[⚠️] Could not connect to Besu")

# Load smart contract
contract = None
if os.path.exists(CONTRACT_INFO_PATH):
    try:
        with open(CONTRACT_INFO_PATH, "r") as f:
            data = json.load(f)
        contract_address = Web3.to_checksum_address(data["address"])
        contract_abi = data["abi"]
        contract = w3.eth.contract(address=contract_address, abi=contract_abi)
        print("[🔗] Contract loaded.")
    except Exception as e:
        print("[⚠️] Failed to load contract:", e)
else:
    print("[⚠️] contract_data.json missing.")

ACCOUNT = w3.eth.account.from_key(PRIVATE_KEY)
clean_tx_counter = 0

# ---------- RE-EVALUATION HELPERS ----------
def _already_flagged(tx):
    """
    Simple duplicate check: compare sender, receiver, amount roughly.
    """
    if not os.path.exists("flagged_log.json"):
        return False
    try:
        with open("flagged_log.json") as f:
            arr = json.load(f)
    except Exception:
        return False
    for a in arr:
        t = a.get("tx", {})
        if (
            t.get("sender") == tx.get("sender")
            and t.get("receiver") == tx.get("receiver")
            and abs(float(t.get("amount", 0)) - float(tx.get("amount", 0))) < 1e-6
        ):
            return True
    return False

def reevaluate_recent_chains(latest_tx=None):
    """
    After every new transaction, check recent transactions (24h) to see if any
    now form a coordinated dispersion–aggregation chain (Rule 35).
    latest_tx: optional dict to scope checks for speed.
    """
    print("\n[♻️ RE-EVALUATION] Checking for coordinated dispersion–aggregation patterns...")
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    now = time.time()
    one_day_ago = now - 24 * 3600

    # Scope candidates (narrow scan if latest_tx given)
    if latest_tx:
        s = latest_tx.get("sender")
        r = latest_tx.get("receiver")
        c.execute('''SELECT sender, receiver, amount, timestamp FROM transactions
                     WHERE timestamp >= ? AND (sender=? OR receiver=?)''', (one_day_ago, s, r))
    else:
        c.execute('''SELECT sender, receiver, amount, timestamp FROM transactions
                     WHERE timestamp >= ?''', (one_day_ago,))
    candidates = c.fetchall() or []

    triggered = 0
    for s, r, amt, ts in candidates:
        tx = {
            "sender": s,
            "receiver": r,
            "amount": amt,
            "timestamps": [ts],
            "path": [s, r],
        }
        try:
            # 🧠 Compute all metrics including linked chain detection
            compute_metrics(tx)
            flagged, matched_rules = rules.evaluate(tx)
        except Exception as e:
            print("[⚠️] Re-eval compute/eval error:", e)
            continue

        if flagged:
            for rule in matched_rules:
                # Target Rule 35 specifically
                if rule.get("id") == 35 or "Coordinated Dispersion" in rule.get("name", ""):
                    if _already_flagged(tx):
                        continue

                    # 🧩 Ensure metrics are included in alert
                    compute_metrics(tx)

                    alert = {
                        "tx": tx,
                        "matched_rules": [rule["name"]],
                        "risk_levels": [rule["risk_level"]],
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
                    }

                    # ✅ Write locally to flagged_log.json
                    try:
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
                    except Exception as e:
                        print("[⚠️] Could not write flagged_log.json during re-eval:", e)

                    print(f"[🚨 RE-EVAL ALERT] Coordinated Dispersion–Aggregation flagged: {s} → {r}")
                    print(f"→ Common receiver: {tx.get('linked_chain_common_receiver')}")
                    print(f"→ Members: {tx.get('linked_chain_members')}")

                    triggered += 1

                    # 🧱 Optional: Send to smart contract on Besu
                    if contract is not None:
                        try:
                            payload = json.dumps({
                                "sender": tx["sender"],
                                "receiver": tx["receiver"],
                                "amount": tx["amount"],
				"path": tx.get("path", []),
				"num_accounts_involved": tx.get("num_accounts_involved", 0),
				"num_layers": tx.get("num_layers", 0),
				"total_amount": tx.get("total_amount", tx["amount"]),
                                "rules_triggered": [rule["name"]],
                                "timestamp": alert["timestamp"],
                                # 👇 Include Rule 35 linkage metadata on-chain
                                "linked_chain_common_receiver": tx.get("linked_chain_common_receiver"),
                                "linked_chain_members": tx.get("linked_chain_members"),
                            })
                            nonce = w3.eth.get_transaction_count(ACCOUNT.address)
                            txn = contract.functions.storeFlaggedTx(payload).build_transaction({
                                "from": ACCOUNT.address,
                                "nonce": nonce,
                                "gas": 2000000,
                                "gasPrice": w3.to_wei("1", "gwei")
                            })
                            signed = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
                            tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                            print(f"[🧱 ON-CHAIN] Re-eval flagged TX sent. Hash: {tx_hash.hex()}")
                        except Exception as e:
                            print("[⚠️] On-chain store failed during re-eval:", e)

                    # ⛏️ Auto-mine block for this flagged TX
                    try:
                        prev_hash = chain.last_block()["hash"]
                        new_block = chain.create_block(prev_hash)
                        print(f"[⛏️ AUTO-MINE] Block #{new_block['index']} created for re-eval flagged TX.")
                        socketio.emit("new_block", new_block)
                    except Exception as e:
                        print("[⚠️] Auto-mine failed during re-eval:", e)

    conn.close()

    if triggered == 0:
        print("[✅ RE-EVALUATION] No new coordinated patterns found.")
    else:
        print(f"[✅ RE-EVALUATION] {triggered} coordinated pattern(s) flagged.")


# ---------- ROUTES ----------
app = Flask(__name__)
CORS(app)

@app.route("/chain", methods=["GET"])
def get_chain():
    return jsonify(chain.chain), 200

@app.route("/mine", methods=["GET"])
def mine():
    prev_hash = chain.last_block()["hash"]
    new_block = chain.create_block(prev_hash)
    socketio.emit("new_block", new_block)
    print(f"[⛏️ MINED] Block #{new_block['index']} created.")
    return jsonify(new_block), 200

@app.route("/add_tx", methods=["POST"])
def add_tx():
    global clean_tx_counter
    # --- read incoming tx and headers
    tx = request.get_json() or {}
    # allow wallet id in header (preferred)
    sender_from_header = request.headers.get("X-Wallet-ID")
    user_email = request.headers.get("X-User-Email")
    if sender_from_header:
        tx["sender"] = sender_from_header

    tx.setdefault("timestamps", [time.time()])
    tx.setdefault("path", [tx.get("sender"), tx.get("receiver")])

    # --------- NEW: Wallet / Balance checks using MySQL ----------
    try:
        import mysql.connector as mysql_conn
        sql_conn = mysql_conn.connect(**MYSQL_CONFIG)
        sql_cur = sql_conn.cursor(dictionary=True)

        sender_wallet = tx.get("sender")
        amount = float(tx.get("amount", 0))

        # 1) Check sender exists
        sql_cur.execute("SELECT balance FROM wallets WHERE wallet_id = %s", (sender_wallet,))
        row = sql_cur.fetchone()
        if not row:
            sql_cur.close(); sql_conn.close()
            return jsonify({"error": "Sender wallet not found"}), 400

        # 2) Check sufficient funds
        if float(row["balance"]) < amount:
            sql_cur.close(); sql_conn.close()
            return jsonify({"error": "Insufficient balance"}), 400

        # 3) Check receiver exists (Rule C: reject if missing)
        receiver_wallet = tx.get("receiver")
        sql_cur.execute("SELECT balance FROM wallets WHERE wallet_id = %s", (receiver_wallet,))
        rrow = sql_cur.fetchone()
        if not rrow:
            sql_cur.close(); sql_conn.close()
            return jsonify({"error": "Receiver wallet not found"},), 400

        # At this point balances are OK; we'll perform atomic update AFTER saving tx.
    except Exception as e:
        print("[⚠️] MySQL balance check error:", e)
        try:
            sql_cur.close()
        except:
            pass
        try:
            sql_conn.close()
        except:
            pass
        return jsonify({"error": "Internal server error - balance check"}), 500

    # 1️⃣ Save first so DB queries include it in metrics (includes links table)
    try:
        # ensure sender present for sqlite record
        save_tx_to_db(tx)
    except Exception as e:
        print("[⚠️] DB save error:", e)
        # do not return here; proceed to compute metrics and evaluation (but we will not update wallets if save fails badly)

    # 2️⃣ Compute metrics AFTER saving
    compute_metrics(tx)

    # 3️⃣ Evaluate AML rules
    try:
        flagged, matched_rules = rules.evaluate(tx)
    except Exception as e:
        print("[⚠️] Rule evaluation failed:", e)
        flagged, matched_rules = False, []

    # ---------- PERFORM MySQL balance transfer (atomic) ----------
    try:
        # Deduct sender (ensures balance check at update time)
        sql_cur.execute(
            "UPDATE wallets SET balance = balance - %s WHERE wallet_id = %s AND balance >= %s",
            (amount, sender_wallet, amount)
        )
        if sql_cur.rowcount == 0:
            # no rows updated -> likely insufficient balance concurrently
            try:
                sql_conn.rollback()
            except:
                pass
            sql_cur.close()
            sql_conn.close()
            return jsonify({"error": "Insufficient balance (concurrent)"}), 400

        # Credit receiver
        sql_cur.execute(
            "UPDATE wallets SET balance = balance + %s WHERE wallet_id = %s",
            (amount, receiver_wallet)
        )
        if sql_cur.rowcount == 0:
            # receiver disappeared (shouldn't happen because we checked earlier) -> rollback
            try:
                sql_conn.rollback()
            except:
                pass
            sql_cur.close()
            sql_conn.close()
            return jsonify({"error": "Receiver wallet missing during transfer"}), 400

        # Commit wallet changes
        sql_conn.commit()
        # close mysql cursor/conn
        sql_cur.close()
        sql_conn.close()
    except Exception as e:
        try:
            sql_conn.rollback()
        except:
            pass
        try:
            sql_cur.close()
        except:
            pass
        try:
            sql_conn.close()
        except:
            pass
        print("[⚠️] Wallet update error:", e)
        return jsonify({"error": "Internal server error - wallet update"}), 500

    # 4️⃣ Always add to blockchain
    idx = chain.add_transaction(tx["sender"], tx["receiver"], tx["amount"], tx.get("data", ""))
    prev_hash = chain.last_block()["hash"]

    if flagged:
        alert = {
        "tx": {
            "sender": tx["sender"],
            "receiver": tx["receiver"],
            "amount": tx["amount"],
            "path": tx.get("path", [tx["sender"], tx["receiver"]]),  # ✅ KEY FIX
            "num_accounts_involved": tx.get("num_accounts_involved", 0),
            "num_layers": tx.get("num_layers", 0),
            "total_amount": tx.get("total_amount", tx["amount"]),
            "timestamps": tx.get("timestamps", []),
            "avg_delay_between_layers": tx.get("avg_delay_between_layers", 0),
            # Rule 35 data
            "linked_chain_common_receiver": tx.get("linked_chain_common_receiver"),
            "linked_chain_members": tx.get("linked_chain_members", []),
        },
        "matched_rules": [r["name"] for r in matched_rules],
        "risk_levels": [r["risk_level"] for r in matched_rules],
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
    }

        # Write to local log
        try:
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
        except Exception as e:
            print("[⚠️] Logging failed:", e)

        print(f"[🚨 ALERT] Suspicious TX flagged: {tx['sender']} → {tx['receiver']} ({tx['amount']})")
        print(f"→ Triggered: {[r['name'] for r in matched_rules]}")

        # On-chain store (optional)
        if contract is not None:
            try:
                payload = json.dumps({
                    "sender": tx["sender"],
                    "receiver": tx["receiver"],
                    "amount": tx["amount"],
                    "path": tx.get("path", []),  # ✅ ADD
                    "num_accounts_involved": tx.get("num_accounts_involved", 0),  # ✅ ADD
                    "num_layers": tx.get("num_layers", 0),  # ✅ ADD
                    "total_amount": tx.get("total_amount", tx["amount"]),  # ✅ ADD
                    "rules_triggered": [r["name"] for r in matched_rules],
                    "timestamp": alert["timestamp"]
                })
                nonce = w3.eth.get_transaction_count(ACCOUNT.address)
                txn = contract.functions.storeFlaggedTx(payload).build_transaction({
                    "from": ACCOUNT.address,
                    "nonce": nonce,
                    "gas": 2000000,
                    "gasPrice": w3.to_wei("1", "gwei")
                })
                signed = w3.eth.account.sign_transaction(txn, PRIVATE_KEY)
                tx_hash = w3.eth.send_raw_transaction(signed.raw_transaction)
                print(f"[🧱 ON-CHAIN] Flagged TX sent. Hash: {tx_hash.hex()}")
            except Exception as e:
                print("[⚠️] On-chain store failed:", e)

        # Auto-mine immediately
        new_block = chain.create_block(prev_hash)
        print(f"[⛏️ AUTO-MINE] Block #{new_block['index']} created for flagged TX.")
        socketio.emit("new_block", new_block)

        # Re-evaluate recent chains (to catch any other now-linked patterns)
        try:
            reevaluate_recent_chains(latest_tx=tx)
        except Exception as e:
            print("[⚠️] Re-evaluation failed after flagged tx:", e)

        return jsonify({
            "status": "flagged",
            "block_index": new_block["index"],
            "triggered_rules": [r["name"] for r in matched_rules]
        }), 200

    # Clean tx handling
    clean_tx_counter += 1
    print(f"[✅ CLEAN] TX: {tx['sender']} → {tx['receiver']} ({tx['amount']})")

    # Post-transaction re-evaluation to catch linked patterns formed by this tx
    try:
        reevaluate_recent_chains(latest_tx=tx)
    except Exception as e:
        print("[⚠️] Re-evaluation failed after clean tx:", e)

    if clean_tx_counter >= CLEAN_MINE_THRESHOLD:
        new_block = chain.create_block(prev_hash)
        print(f"[⛏️ AUTO-MINE] Clean threshold reached → Block #{new_block['index']}")
        socketio.emit("new_block", new_block)
        clean_tx_counter = 0

    return jsonify({"status": "clean", "block_index": idx}), 201

# ---------- SOCKET ----------
@socketio.on("new_block")
def sync_block(block):
    chain.chain.append(block)

# ---------- MAIN ----------
if __name__ == "__main__":
    print("Miner running on port 5000 (Monitoring + Rule-based Detection + Auto-Link + Re-Eval)")
    socketio.run(app, host="0.0.0.0", port=5000)