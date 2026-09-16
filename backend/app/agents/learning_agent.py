"""
===========================================================
Learning Agent
-----------------------------------------------------------
Lightweight feedback loop: whenever a human corrects an
order (e.g. via the dashboard), this agent stores the
correction in a JSON log. Over time this log can be used to
fine-tune prompts or build a lookup cache for the Recovery
Agent (e.g. "this customer's PO numbers always start with
PO-"), which is a great talking point for the presentation
even in a lightweight prototype.
===========================================================
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Dict

LOG_PATH = Path(__file__).resolve().parent.parent.parent / "logs" / "learning_log.jsonl"


class LearningAgent:

    def record_correction(self, order_id: int, field: str, old_value, new_value) -> Dict:

        LOG_PATH.parent.mkdir(parents=True, exist_ok=True)

        entry = {
            "order_id": order_id,
            "field": field,
            "old_value": old_value,
            "new_value": new_value,
            "timestamp": datetime.utcnow().isoformat(),
        }

        with open(LOG_PATH, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

        return {"agent": "LearningAgent", "status": "recorded", "entry": entry}

    def get_corrections_for_field(self, field: str) -> list:

        if not LOG_PATH.exists():
            return []

        results = []
        with open(LOG_PATH, "r", encoding="utf-8") as f:
            for line in f:
                entry = json.loads(line)
                if entry["field"] == field:
                    results.append(entry)

        return results
