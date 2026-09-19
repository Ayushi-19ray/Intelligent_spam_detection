
import json

import db
from agents import manager, reporter_agent

db.init_db()

with open("sample_data/sample_messages.json") as f:
    samples = json.load(f)

for i, sample in enumerate(samples, 1):
    print(f"\n\n########## SAMPLE {i}/{len(samples)} ##########")
    report = manager.analyze_message(
        text=sample["text"],
        sender=sample.get("sender"),
        channel=sample.get("channel", "email"),
        metadata=sample.get("metadata", {}),
    )
    print(reporter_agent.pretty_print(report))

print("\n\nDone. Run `python main.py stats` to see stored profiles and decisions.")
