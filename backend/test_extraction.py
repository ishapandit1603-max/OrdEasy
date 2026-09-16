"""
Quick standalone test for the Extraction Agent, without going
through the FastAPI upload pipeline. Useful for confirming your
OPENAI_API_KEY works before wiring up the full app.

Run with:
    python test_extraction.py
"""

from pathlib import Path
from app.agents.extraction_agent import ExtractionAgent

sample_text = Path("sample_data/sample_po.txt").read_text(encoding="utf-8")

agent = ExtractionAgent()
result = agent.extract(sample_text)

import json
print(json.dumps(result, indent=2))
