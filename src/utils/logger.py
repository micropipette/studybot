import logging


logger = logging.getLogger("ComradeLog")
logger.setLevel(logging.INFO)

# Configure loggers
c_handler = logging.StreamHandler()
f_handler = logging.FileHandler(
    filename="studybot.log", mode="w", encoding="utf-8")
c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.INFO)

c_format = logging.Formatter('%(asctime)s: %(message)s',
                             datefmt="%H:%M:%S")
f_format = logging.Formatter('%(asctime)s: %(levelname)s - %(message)s',
                             datefmt="%I:%M:%S %p %Z")

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

logger.addHandler(c_handler)
logger.addHandler(f_handler)
