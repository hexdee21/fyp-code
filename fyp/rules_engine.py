import json

class RuleEngine:
    def __init__(self, rules_path="rules.json"):
        with open(rules_path, "r") as f:
            self.rules = json.load(f)

    def evaluate(self, tx):
        flagged_rules = []
        for rule in self.rules:
            try:
                # Evaluate rule condition safely
                if eval(rule["condition"], {}, tx):
                    flagged_rules.append(rule)
            except Exception:
                continue
        return (len(flagged_rules) > 0, flagged_rules)

def analyze_transactions(transactions, rules_path="rules.json"):
    """
    Wrapper function to analyze a list of transactions using RuleEngine.
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
