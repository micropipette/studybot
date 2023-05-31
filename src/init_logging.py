# Sourced from https://github.com/NAFTeam/Bot-Template/blob/main/%7B%7B%20cookiecutter.project_slug%20%7D%7D/core/init_logging.py
import logging
import os
import time
from typing import Optional

from interactions import logger_name


class CustomLogger:
    """Log all errors to a file, and log all logging events to console"""

    def __init__(self):
        self.formatter = logging.Formatter(
            "%(asctime)s UTC || %(levelname)s || %(message)s"
        )
        self.formatter.converter = time.gmtime

    def make_logger(self, log_name: str):
        logger = logging.getLogger(log_name)
        logger.setLevel(logging.DEBUG)

        # log to console
        console_handler = logging.StreamHandler()
        console_handler.setFormatter(self.formatter)
        console_handler.setLevel(logging.INFO)

        # log to file
        file_handler = MakeFileHandler(
            filename="./studybot.log",
            encoding="utf-8",
        )
        file_handler.setFormatter(self.formatter)
        file_handler.setLevel(logging.ERROR)

        # add bother handlers
        logger.addHandler(console_handler)
        logger.addHandler(file_handler)


class MakeFileHandler(logging.FileHandler):
    """Subclass of logging.FileHandler which makes sure the folder is created"""

    def __init__(
        self,
        filename: str,
        mode: str = "a",
        encoding: Optional[str] = None,
        delay: bool = False,
    ):
        # create the folder if it does not exist already
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        logging.FileHandler.__init__(self, filename, mode, encoding, delay)


def init_logging():
    # Initialize formatter
    logger = CustomLogger()

    # Initialize logging for exceptions
    logger.make_logger(logger_name)
