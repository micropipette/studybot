from flask import Flask, render_template, send_file
# used to create web server to keep bot actively hosted
from threading import Thread
# used to create separate parallel process to keep bot up

import logging
import os

from utils.utilities import get_uptime
from utils.logger import logger
from client import client as bot
import datetime
from config import version

# disable flask dumb logging
logging.getLogger('werkzeug').disabled = True
os.environ['WERKZEUG_RUN_MAIN'] = 'true'

app = Flask('')


@app.route('/')
def main():

    with open("bot.log", "r", encoding="utf-8") as f:
        content = f.read().splitlines()

    uptime = datetime.timedelta(seconds=round(get_uptime()))

    return render_template("index.html", uptime=str(uptime),
                           numservers=len(bot.guilds),
                           user=str(bot.user), serverlist=[f"{server.name} "
                           f"({len(server.members)} members)"
                                                           for server in bot.guilds],
                           loglines=content,
                           version=version)


@app.route('/log')
def downloadFile():
    path = "bot.log"
    return send_file(path, as_attachment=True,
                     attachment_filename='comrade_log.txt')


def run():
    app.run(host="0.0.0.0", port=8080)


def keep_alive():
    server = Thread(target=run)
    server.daemon = True
    server.start()
    logger.info("Flask server started.")


'''
Ping the url using something like https://uptimerobot.com/
This will keep things like repl.it up
'''
