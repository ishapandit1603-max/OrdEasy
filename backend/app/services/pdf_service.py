"""
===========================================================
PDF Service
-----------------------------------------------------------
Reads a PDF file page by page using PyMuPDF (fitz) and
returns the combined text plus basic metadata.
===========================================================
"""

import os
from typing import Dict

from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()

try:
    import fitz  # PyMuPDF
except ImportError:  # pragma: no cover
    fitz = None


class PDFService:

    def __init__(self):
        if fitz is None:
            logger.warning("PyMuPDF not installed. Run: pip install PyMuPDF")

    def extract_text(self, file_path: str) -> Dict:

        if not os.path.exists(file_path):
            return {"status": "failed", "message": "PDF file not found."}

        if fitz is None:
            return {"status": "failed", "message": "PyMuPDF is not installed."}

        try:
            pdf = fitz.open(file_path)

            full_text = ""
            for page_number in range(pdf.page_count):
                page = pdf.load_page(page_number)
                full_text += page.get_text() + "\n"

            metadata = {
                "title": pdf.metadata.get("title"),
                "author": pdf.metadata.get("author"),
                "pages": pdf.page_count,
            }

            pdf.close()

            return {
                "status": "success",
                "document_type": "pdf",
                "text": full_text.strip(),
                "metadata": metadata,
            }

        except Exception as e:
            logger.error(f"PDF extraction failed: {e}")
            return {"status": "failed", "message": str(e)}
