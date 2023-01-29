import asyncio
import os

import dotenv
import topgg
from naff import (Activity, AutoShardedClient, Intents, IntervalTrigger, Task,
                  listen)

from config import cfg
from db import mongo_startup

dotenv.load_dotenv()  # Load .env file, prior to components loading

mongo_startup()

activity = Activity.create(name="helping you study!")

bot = AutoShardedClient(intents=Intents.new(
                        guilds=True,
                        direct_messages=True
                        ), sync_interactions=True, activity=activity,
                        total_shards=int(cfg["Settings"]["shard-count"]))

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
            guild_count=len(bot.guilds),
            shard_count=bot.total_shards)
        print(f"Updated guild count to {len(bot.guilds)}")
    except BaseException:
        print(msg="Failed to update guild count")


@listen()
async def on_ready():
    print(f"{bot.user.username} is online.")
    update_guild_count.start()

# Locate and load all modules under "modules"
bot.load_extension("modules.general")
bot.load_extension("modules.quiz")

bot.start(os.environ.get("TOKEN"))
