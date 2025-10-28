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
