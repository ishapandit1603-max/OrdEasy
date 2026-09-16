"""
===========================================================
Logger Service
-----------------------------------------------------------
Centralized logging for every service and agent.
Writes to both console and a daily log file under /logs.
===========================================================
"""

import logging
import os
from datetime import datetime

from app.config import settings


class LoggerService:

    _logger = None

    @classmethod
    def get_logger(cls) -> logging.Logger:

        if cls._logger:
            return cls._logger

        if not os.path.exists(settings.LOG_DIR):
            os.makedirs(settings.LOG_DIR)

        log_filename = datetime.now().strftime("%Y-%m-%d") + ".log"
        log_path = os.path.join(settings.LOG_DIR, log_filename)

        logger = logging.getLogger("OrdEasy")
        logger.setLevel(logging.INFO)
        logger.handlers.clear()

        formatter = logging.Formatter(
            "%(asctime)s | %(levelname)s | %(name)s | %(message)s"
        )

        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)

        console_handler = logging.StreamHandler()
        console_handler.setFormatter(formatter)

        logger.addHandler(file_handler)
        logger.addHandler(console_handler)

        cls._logger = logger
        return logger

    @classmethod
    def info(cls, message: str):
        cls.get_logger().info(message)

    @classmethod
    def warning(cls, message: str):
        cls.get_logger().warning(message)

    @classmethod
    def error(cls, message: str):
        cls.get_logger().error(message)

    @classmethod
    def debug(cls, message: str):
        cls.get_logger().debug(message)
