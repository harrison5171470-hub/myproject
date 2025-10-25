

rules = [
    {"condition": lambda x: x["age"] < 25 and x["amount"] > 1000, "action": "10% discount"},
    {"condition": lambda x: x["vip"], "action": "Extra 5% discount"}
]

customer = {"age": 22, "amount": 1200, "vip": True}

for rule in rules:
    if rule["condition"](customer):
        print("Apply:", rule["action"])