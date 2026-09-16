"""
===========================================================
OCR Service
-----------------------------------------------------------
Extracts text from scanned images (PNG/JPG/etc.) using
PaddleOCR. This dependency is heavy (~500MB with models), so
it is imported lazily: the rest of the system works fine
even if PaddleOCR is not installed, and this service simply
reports a clear error instead of crashing the whole app.

Install with:
    pip install paddlepaddle paddleocr opencv-python-headless
===========================================================
"""

import os
from typing import Dict

from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()

_ocr_engine = None


def _get_ocr_engine():
    global _ocr_engine
    if _ocr_engine is None:
        from paddleocr import PaddleOCR  # imported lazily on purpose
        _ocr_engine = PaddleOCR(use_angle_cls=True, lang="en", show_log=False)
    return _ocr_engine


class OCRService:

    def extract_text(self, file_path: str) -> Dict:

        if not os.path.exists(file_path):
            return {"status": "failed", "message": "Image file not found."}

        try:
            engine = _get_ocr_engine()
        except ImportError:
            logger.error("PaddleOCR is not installed.")
            return {
                "status": "failed",
                "message": (
                    "PaddleOCR is not installed. Run: "
                    "pip install paddlepaddle paddleocr opencv-python-headless"
                ),
            }
        except Exception as e:
            logger.error(f"Failed to initialize OCR engine: {e}")
            return {"status": "failed", "message": str(e)}

        try:
            result = engine.ocr(file_path, cls=True)

            lines = []
            for block in result:
                for line in block:
                    text = line[1][0]
                    confidence = line[1][1]
                    lines.append((text, confidence))

            full_text = "\n".join(text for text, _ in lines)
            avg_confidence = (
                sum(c for _, c in lines) / len(lines) if lines else 0.0
            )

            return {
                "status": "success",
                "document_type": "image",
                "text": full_text.strip(),
                "metadata": {
                    "line_count": len(lines),
                    "average_ocr_confidence": round(avg_confidence, 3),
                },
            }

        except Exception as e:
            logger.error(f"OCR extraction failed: {e}")
            return {"status": "failed", "message": str(e)}
