"""
===========================================================
Excel Service
-----------------------------------------------------------
Reads .xlsx / .xls / .csv files and converts every row into
JSON, plus a flattened text representation so the same
Extraction Agent + OpenAI prompt can be reused for Excel
orders as well as PDFs.
===========================================================
"""

import os
from pathlib import Path
from typing import Dict

import pandas as pd

from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()


class ExcelService:

    def read_file(self, file_path: str) -> pd.DataFrame:

        extension = Path(file_path).suffix.lower()

        if extension == ".csv":
            return pd.read_csv(file_path)

        return pd.read_excel(file_path)

    def extract_text(self, file_path: str) -> Dict:
        """
        Returns both structured rows (JSON) and a plain-text
        version of the sheet, so it can be fed straight into
        the same Extraction Agent prompt used for PDFs.
        """

        if not os.path.exists(file_path):
            return {"status": "failed", "message": "Excel file not found."}

        try:
            df = self.read_file(file_path)

            df = df.dropna(how="all")

            rows = df.to_dict(orient="records")

            # Build a plain-text table so OpenAI can read it
            # the same way it reads a PDF's raw text.
            text_lines = [", ".join(str(c) for c in df.columns)]
            for row in rows:
                text_lines.append(
                    ", ".join(f"{k}: {v}" for k, v in row.items())
                )

            combined_text = "\n".join(text_lines)

            return {
                "status": "success",
                "document_type": "excel",
                "text": combined_text,
                "rows": rows,
                "metadata": {
                    "row_count": len(rows),
                    "columns": list(df.columns),
                },
            }

        except Exception as e:
            logger.error(f"Excel extraction failed: {e}")
            return {"status": "failed", "message": str(e)}
