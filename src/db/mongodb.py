'''
MongoDB Database for Studybot
'''
import os
import sys
from logging import getLogger

import pymongo
from interactions import logger_name
from pymongo.collection import Collection

from config import cfg

mongo_client = None
db = None


def startup():
    '''
    Runs during startup to set up the databases
    The rationale is to defer execution until .env is loaded
    '''
    global mongo_client, db
    logger = getLogger(logger_name)

    try:
        mongo_client = pymongo.MongoClient(os.environ.get("MONGOKEY"))
    except Exception as e:
        logger.exception(e)
        logger.error("MongoDB Could not be connected. Check that you have "
                     "the correct MongoDB key in your .env file, and "
                     "the that you have dnspython installed"
                     "\nTerminating program...")
        sys.exit(1)  # Exit with error

    db = mongo_client[mongo_client.list_database_names()[0]]
    logger.info("MongoDB Atlas connected to: "
                f"{mongo_client.list_database_names()[0]}")


# Convenience method to return collection by name in configuration
def collection(name) -> Collection:
    try:
        return db[cfg["MongoDB"][name]]
    except Exception:
        return None
