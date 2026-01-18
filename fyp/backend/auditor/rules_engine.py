import json

class RuleEngine:
    def __init__(self, rules_path="rules.json"):
        with open(rules_path, "r") as f:
            self.rules = json.load(f)

    def evaluate(self, tx, context=None):
        """
        Evaluate a single transaction against all rules.
        'context' can include other transactions (e.g., for dispersion/aggregation checks).
        """
        flagged_rules = []
        tx_context = context or {}

        for rule in self.rules:
            try:
                # Safe evaluation context (no builtins)
                local_ctx = {**tx, **tx_context}
                if eval(rule["condition"], {}, local_ctx):
                    flagged_rules.append(rule)
            except Exception as e:
                continue

        return (len(flagged_rules) > 0, flagged_rules)


def analyze_transactions(transactions, rules_path="rules.json"):
    """
    Analyze a list of transactions using RuleEngine.
    Returns a list of flagged transactions with triggered rules.
    """
    engine = RuleEngine(rules_path)
    flagged = []

    for tx in transactions:
        is_flagged, matched_rules = engine.evaluate(tx)
        if is_flagged:
            flagged.append({
                "transaction": tx,
                "violated_rules": matched_rules
            })
    return flagged


# -------------------------------------------------------------------------
# 🧠 ADVANCED ANALYSIS – Rule 35 (Coordinated Dispersion–Aggregation)
# -------------------------------------------------------------------------
def detect_linked_dispersion_aggregation(transactions):
    """
    Detects coordinated dispersion → aggregation chains (Rule 35).

    Logic:
    - If multiple transactions have the same sender → multiple receivers (dispersion),
      and later those receivers send funds to a common receiver (aggregation),
      the entire network is flagged as coordinated.

    Returns:
        {
          "is_linked_chain": bool,
          "linked_chain_members": set(),
          "linked_chain_common_receiver": str or None,
          "linked_chain_txs": list of dicts
        }
    """

    # Build maps
    senders = {}
    receivers = {}
    for tx in transactions:
        s, r = tx["sender"], tx["receiver"]
        senders.setdefault(s, []).append(tx)
        receivers.setdefault(r, []).append(tx)

    linked_chain_txs = []
    linked_chain_members = set()
    linked_chain_common_receiver = None

    # Step 1: Find dispersion — one sender to 3+ receivers
    dispersion_senders = [s for s, txs in senders.items() if len(txs) >= 3]

    # Step 2: Check aggregation — those receivers funnel to a common receiver
    for ds in dispersion_senders:
        recv_list = [t["receiver"] for t in senders[ds]]
        next_hops = [t for t in transactions if t["sender"] in recv_list]

        if not next_hops:
            continue

        agg_targets = [t["receiver"] for t in next_hops]
        for target in agg_targets:
            if agg_targets.count(target) >= 3:
                linked_chain_common_receiver = target
                linked_chain_txs = senders[ds] + [t for t in next_hops if t["receiver"] == target]
                linked_chain_members = {ds, *recv_list, target}

                return {
                    "is_linked_chain": True,
                    "linked_chain_members": linked_chain_members,
                    "linked_chain_common_receiver": linked_chain_common_receiver,
                    "linked_chain_txs": linked_chain_txs
                }

    return {
        "is_linked_chain": False,
        "linked_chain_members": set(),
        "linked_chain_common_receiver": None,
        "linked_chain_txs": []
    }


# -------------------------------------------------------------------------
# 🧩 Combined Transaction Analyzer (with Rule 35 integration)
# -------------------------------------------------------------------------
def analyze_all_rules(transactions, rules_path="rules.json"):
    """
    Runs all basic + advanced AML rules, including Rule 35 (coordinated pattern).
    """

    engine = RuleEngine(rules_path)
    flagged = []

    # First, evaluate simple rules
    for tx in transactions:
        is_flagged, matched_rules = engine.evaluate(tx)
        if is_flagged:
            flagged.append({
                "transaction": tx,
                "violated_rules": matched_rules
            })

    # Then detect coordinated dispersion–aggregation
    linked = detect_linked_dispersion_aggregation(transactions)
    if linked["is_linked_chain"] and len(linked["linked_chain_members"]) >= 4:
        flagged.append({
            "transaction": {
                "pattern": "Coordinated Dispersion-Aggregation",
                "receiver": linked["linked_chain_common_receiver"]
            },
            "violated_rules": [{
                "id": 35,
                "name": "Coordinated Dispersion-Aggregation Detected",
                "risk_level": "Critical",
                "category": "Layering",
                "action": "flag_layering"
            }],
            "linked_chain": {
                "members": list(linked["linked_chain_members"]),
                "edges": [(t["sender"], t["receiver"]) for t in linked["linked_chain_txs"]]
            }
        })

    return flagged


# -------------------------------------------------------------------------
# 🧪 Example (for quick testing)
# -------------------------------------------------------------------------
if __name__ == "__main__":
    sample_txs = [
        {"sender": "Naveed_Ahmed", "receiver": "Raza_Khan", "amount": 42000},
        {"sender": "Naveed_Ahmed", "receiver": "Salman_Shah", "amount": 39000},
        {"sender": "Naveed_Ahmed", "receiver": "Adeel_Butt", "amount": 41000},
        {"sender": "Raza_Khan", "receiver": "Zara_Iqbal", "amount": 42000},
        {"sender": "Salman_Shah", "receiver": "Zara_Iqbal", "amount": 39000},
        {"sender": "Adeel_Butt", "receiver": "Zara_Iqbal", "amount": 41000}
    ]

    flagged = analyze_all_rules(sample_txs)
    print(json.dumps(flagged, indent=2))
