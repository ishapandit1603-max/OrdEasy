"""
===========================================================
Extraction Agent
-----------------------------------------------------------
Sends raw document text (from PDF/Excel/OCR) to OpenAI using
the shared extraction_prompt.txt, and parses the response
into structured order JSON. Works the same way regardless of
which document type the text originally came from.
===========================================================
"""

import json
from pathlib import Path
from typing import Dict

from app.services.openai_service import ask_openai
from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()

PROMPT_PATH = Path(__file__).resolve().parent.parent / "prompts" / "extraction_prompt.txt"


class ExtractionAgent:

    def __init__(self):
        self.system_prompt = PROMPT_PATH.read_text(encoding="utf-8")

    def build_prompt(self, document_text: str) -> str:
        return f"{self.system_prompt}\n\n================ DOCUMENT ================\n\n{document_text}\n\n==========================================\n"

    @staticmethod
    def _clean_json_text(raw: str) -> str:
        cleaned = raw.strip()
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            cleaned = cleaned.replace("json", "", 1).strip()
        return cleaned

    def extract(self, document_text: str) -> Dict:

        if not document_text or not document_text.strip():
            return {
                "agent": "ExtractionAgent",
                "status": "failed",
                "message": "No text provided to extract from.",
            }

        prompt = self.build_prompt(document_text)

        try:
            raw_response = ask_openai(prompt)
            cleaned = self._clean_json_text(raw_response)
            data = json.loads(cleaned)

            logger.info("Extraction Agent: parsed JSON successfully")

            return {
                "agent": "ExtractionAgent",
                "status": "success",
                "data": data,
            }

        except json.JSONDecodeError:
            logger.error("Extraction Agent: OpenAI did not return valid JSON")
            return {
                "agent": "ExtractionAgent",
                "status": "failed",
                "message": "OpenAI did not return valid JSON.",
                "raw_output": raw_response if "raw_response" in locals() else None,
            }

        except Exception as e:
            logger.error(f"Extraction Agent failed: {e}")
            return {"agent": "ExtractionAgent", "status": "failed", "message": str(e)}
