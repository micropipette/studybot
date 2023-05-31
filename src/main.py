import asyncio
import os

import dotenv
import topgg
from interactions import (
    Activity,
    AutoShardedClient,
    Intents,
    IntervalTrigger,
    Task,
    listen,
    const,
)

from config import cfg
from db import mongo_startup
from init_logging import init_logging

dotenv.load_dotenv()  # Load .env file, prior to components loading

init_logging()

mongo_startup()

activity = Activity.create(name="helping you study!")

bot = AutoShardedClient(
    intents=Intents.new(guilds=True, direct_messages=True),
    sync_interactions=True,
    activity=activity,
    total_shards=int(cfg["Settings"]["shard-count"]),
)

# We need to monkeypatch in a ".loop" attribute to the bot, which is used by topgg
# Create a new asyncio loop and assign it to the bot
bot.loop = asyncio.new_event_loop()

# Monkeypatch in a top.gg client
bot.topgg = topgg.DBLClient(bot, os.environ.get("TOPGG"))
# top.gg client to push server count


@Task.create(IntervalTrigger(minutes=30))
async def update_guild_count():
    try:
        await bot.topgg.post_guild_count(
            guild_count=len(bot.guilds), shard_count=bot.total_shards
        )
        bot.logger.info(f"Updated guild count to {len(bot.guilds)}")
    except BaseException:
        bot.logger.warning("Failed to update guild count")


# Temporary workaround while discord api is broken
const.CLIENT_FEATURE_FLAGS["FOLLOWUP_INTERACTIONS_FOR_IMAGES"] = True


@listen()
async def on_ready():
    bot.logger.info(f"Logged in as {bot.user}")
    update_guild_count.start()


# Locate and load all modules under "modules"
bot.load_extension("modules.general")
bot.load_extension("modules.quiz")

bot.start(os.environ.get("TOKEN"))
