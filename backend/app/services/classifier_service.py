"""
===========================================================
Classifier Service
-----------------------------------------------------------
Decides what kind of document was uploaded (pdf / excel /
image / email) and which service should process it next.
Used by the Intake Agent.
===========================================================
"""

from pathlib import Path


class ClassifierService:

    FILE_TYPES = {
        ".pdf": "pdf",
        ".png": "image",
        ".jpg": "image",
        ".jpeg": "image",
        ".bmp": "image",
        ".tiff": "image",
        ".xlsx": "excel",
        ".xls": "excel",
        ".csv": "excel",
        ".eml": "email",
    }

    ROUTES = {
        "pdf": "pdf_service",
        "excel": "excel_service",
        "image": "ocr_service",
        "email": "email_service",
    }

    @classmethod
    def classify(cls, file_path: str) -> dict:

        extension = Path(file_path).suffix.lower()

        if extension not in cls.FILE_TYPES:
            return {
                "status": "error",
                "message": f"Unsupported file type: {extension}",
            }

        document_type = cls.FILE_TYPES[extension]

        return {
            "status": "success",
            "document_type": document_type,
            "next_service": cls.ROUTES[document_type],
            "file_extension": extension,
        }
