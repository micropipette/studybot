import logging
from datetime import datetime
from dis_snek.const import logger_name

logging.Formatter.converter = \
    lambda *args: datetime.now().timetuple()

log = logging.getLogger("StudyLog")
log.setLevel(logging.DEBUG)

# Configure logs
c_handler = logging.StreamHandler()
# Console output
f_handler = logging.FileHandler(
    filename="studybot.log", mode="w", encoding="utf-8")
# Primary Log

c_handler.setLevel(logging.INFO)
f_handler.setLevel(logging.DEBUG)

c_format = logging.Formatter('%(asctime)s: %(message)s',
                             datefmt="%H:%M:%S")
f_format = logging.Formatter('%(asctime)s [%(filename)s@%(lineno)d (%(funcName)s)]: %(levelname)s - %(message)s',
                             datefmt="%I:%M:%S %p")

c_handler.setFormatter(c_format)
f_handler.setFormatter(f_format)

log.addHandler(c_handler)
log.addHandler(f_handler)

logging.getLogger(logger_name).setLevel(logging.INFO)
logging.getLogger(logger_name).addHandler(f_handler)
