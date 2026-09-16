"""
===========================================================
Intake Agent
-----------------------------------------------------------
First stop for every uploaded file. Confirms the file
exists, classifies its type via ClassifierService, and
returns metadata telling the caller which service to invoke
next. Does no content extraction itself.
===========================================================
"""

import os
from pathlib import Path
from typing import Dict

from app.services.classifier_service import ClassifierService
from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()


class IntakeAgent:

    def __init__(self):
        self.classifier = ClassifierService()

    def process(self, file_path: str) -> Dict:

        if not os.path.exists(file_path):
            logger.error(f"Intake: file not found -> {file_path}")
            return {"agent": "IntakeAgent", "status": "error", "message": "File not found."}

        classification = self.classifier.classify(file_path)

        if classification["status"] == "error":
            logger.warning(f"Intake: unsupported file -> {file_path}")
            return {"agent": "IntakeAgent", "status": "error", "message": classification["message"]}

        file_size = os.path.getsize(file_path)

        result = {
            "agent": "IntakeAgent",
            "status": "success",
            "file_name": Path(file_path).name,
            "file_path": file_path,
            "file_size_bytes": file_size,
            "document_type": classification["document_type"],
            "next_service": classification["next_service"],
        }

        logger.info(f"Intake: {result['file_name']} classified as {result['document_type']}")

        return result
