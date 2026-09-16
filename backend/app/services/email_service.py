"""
===========================================================
Email Service
-----------------------------------------------------------
Connects to an inbox over IMAP (works with Gmail, Outlook,
Yahoo, or any provider that supports IMAP + app passwords -
all free, no API billing). Downloads attachments in
supported formats (pdf, xlsx, xls, csv, png, jpg) from
unread emails, saves them to the uploads folder, and marks
the emails as read so they aren't processed twice.

This is what makes "orders arrive by email" possible without
needing the Gmail API / OAuth consent screen setup - IMAP +
an app password is the simplest free path.
===========================================================
"""

import email
import imaplib
import os
from email.header import decode_header
from pathlib import Path
from typing import List

from app.config import settings
from app.services.logger_service import LoggerService

logger = LoggerService.get_logger()

SUPPORTED_EXTENSIONS = {".pdf", ".xlsx", ".xls", ".csv", ".png", ".jpg", ".jpeg"}

FOLDER_MAP = {
    ".pdf": "pdfs",
    ".xlsx": "excel", ".xls": "excel", ".csv": "excel",
    ".png": "images", ".jpg": "images", ".jpeg": "images",
}


class EmailService:

    def __init__(self):
        self.host = settings.EMAIL_HOST
        self.user = settings.EMAIL_USER
        self.password = settings.EMAIL_PASS
        self.folder = settings.EMAIL_FOLDER

    def _decode(self, value) -> str:
        if value is None:
            return ""
        parts = decode_header(value)
        decoded = ""
        for text, charset in parts:
            if isinstance(text, bytes):
                decoded += text.decode(charset or "utf-8", errors="ignore")
            else:
                decoded += text
        return decoded

    def fetch_new_attachments(self) -> List[str]:
        """
        Connects, finds unread emails, saves any supported attachments,
        marks those emails as read, and returns the list of saved file paths.

        An email is only marked as read if we found and saved at least one
        supported attachment from it. If no supported attachment is found,
        it's left unread so you can inspect it (e.g. it had an unsupported
        file type, or no attachment at all) without silently losing it.
        """

        if not self.user or not self.password:
            logger.warning("Email Service: EMAIL_USER / EMAIL_PASS not configured, skipping.")
            return []

        saved_paths: List[str] = []

        try:
            imap = imaplib.IMAP4_SSL(self.host)
            imap.login(self.user, self.password)
            imap.select(self.folder)

            status, message_ids = imap.search(None, "UNSEEN")
            if status != "OK":
                logger.warning("Email Service: search failed.")
                imap.logout()
                return []

            id_list = message_ids[0].split()
            logger.info(f"Email Service: found {len(id_list)} unread email(s).")

            for msg_id in id_list:
                status, msg_data = imap.fetch(msg_id, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = msg_data[0][1]
                msg = email.message_from_bytes(raw_email)
                subject = self._decode(msg.get("Subject"))
                sender = self._decode(msg.get("From"))

                found_attachment_in_this_email = False

                for part in msg.walk():
                    # Skip container parts - multipart/* wrappers, and the
                    # plain text/html body of the email itself (these have
                    # no filename and aren't real attachments).
                    if part.get_content_maintype() == "multipart":
                        continue

                    filename = self._decode(part.get_filename())
                    if not filename:
                        continue

                    # NOTE: deliberately NOT checking get_content_disposition()
                    # here. Gmail tends to set it to "attachment", but Outlook,
                    # Yahoo, and many mobile mail clients either omit it or set
                    # it to "inline" for files that are still real attachments.
                    # Filtering on it caused attachments from non-Gmail senders
                    # to be silently skipped. Presence of a filename is a more
                    # reliable signal that this part is a real attachment.

                    extension = Path(filename).suffix.lower()

                    logger.info(
                        f"Email Service: email from '{sender}' subject '{subject}' - "
                        f"found part content-type={part.get_content_type()}, "
                        f"disposition={part.get_content_disposition()}, filename={filename!r}"
                    )

                    if extension not in SUPPORTED_EXTENSIONS:
                        logger.info(
                            f"Email Service: skipping unsupported attachment "
                            f"'{filename}' ({extension}) from '{sender}'"
                        )
                        continue

                    folder = FOLDER_MAP.get(extension, "misc")
                    save_dir = os.path.join(settings.UPLOAD_DIR, folder)
                    os.makedirs(save_dir, exist_ok=True)

                    save_path = os.path.join(save_dir, filename)
                    payload = part.get_payload(decode=True)
                    if not payload:
                        logger.warning(f"Email Service: '{filename}' had empty payload, skipping.")
                        continue

                    with open(save_path, "wb") as f:
                        f.write(payload)

                    saved_paths.append(save_path)
                    found_attachment_in_this_email = True
                    logger.info(f"Email Service: saved attachment '{filename}' from '{sender}' ({subject})")

                if found_attachment_in_this_email:
                    # Only mark read if we actually captured something -
                    # otherwise leave it unread so it's retried next poll
                    # and so you can see it in your inbox to investigate.
                    imap.store(msg_id, "+FLAGS", "\\Seen")
                else:
                    logger.warning(
                        f"Email Service: no supported attachment found in email "
                        f"from '{sender}' subject '{subject}' - leaving unread."
                    )

            imap.logout()

        except Exception as e:
            logger.error(f"Email Service: failed to fetch emails - {e}")

        return saved_paths