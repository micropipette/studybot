import dotenv
import os
import time

import components
from client import client as bot
from config import cfg
from hosting.keep_alive import keep_alive
from utils.utilities import set_start_time, get_uptime
from utils.logger import logger


dotenv.load_dotenv()  # Load .env file, prior to components loading

# Startup operations
set_start_time(time.perf_counter())

for c in components.cogs:
    bot.add_cog(c(bot))

online = False


@bot.event
async def on_connect():
    '''
    Connected to Discord
    '''
    logger.info(
        f"{bot.user} is online, logged into {len(bot.guilds)} server(s).")


@bot.event
async def on_ready():
    '''
    Message cache etc. is ready
    '''

    logger.info("Server List:\n" +
                "\n".join(
                    f"\t{server.name} "
                    f"({len(server.members)} members)"
                    for server in bot.guilds))

    logger.info(f"Startup completed in {round(get_uptime(),3)}s")

if cfg["Hosting"]["ping"] == "True":
    keep_alive()

bot.run(os.environ.get("TOKEN"))  # Run bot with loaded password
