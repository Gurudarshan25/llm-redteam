import json
from core import DEFENSES, run_conversation, check_leak

REPEATS = 3
LEVELS_TO_TEST = ["2. hardened prompt", "3. full defense"]

with open("attacks_advanced.json", "r", encoding="utf-8") as f:
    attacks = json.load(f)

results = []

for level in LEVELS_TO_TEST:
    defense = DEFENSES[level]
    print()
    print("==========", level.upper(), "==========")

    for attack in attacks:
        turns = attack.get("turns", [attack.get("prompt")])
        leak_count = 0

        for i in range(REPEATS):
            answers = run_conversation(turns, defense)

            leak_type = None
            for answer in answers:
                leak_type = check_leak(answer)
                if leak_type:
                    break

            if leak_type:
                leak_count += 1

            results.append({
                "defense": level,
                "category": attack["category"],
                "name": attack["name"],
                "try": i + 1,
                "answers": answers,
                "leak_type": leak_type,
            })

        print(f"[{attack['category']}] {attack['name']}: {leak_count}/{REPEATS} leaked")

print()
print("=== ADVANCED ATTACK COMPARISON ===")
for level in LEVELS_TO_TEST:
    tries = [r for r in results if r["defense"] == level]
    leaks = sum(1 for r in tries if r["leak_type"])
    print(f"{level}: {leaks}/{len(tries)} leaked ({leaks / len(tries) * 100:.0f}%)")

with open("results_advanced.json", "w", encoding="utf-8") as f:
    json.dump(results, f, indent=2)

print("Saved to results_advanced.json")