import dotenv
import os

from naff import (Intents, listen, AutoShardedClient,
                  Activity, Task, IntervalTrigger)
import topgg
from db import mongo_startup
from config import cfg

dotenv.load_dotenv()  # Load .env file, prior to components loading

mongo_startup()

activity = Activity.create(name="helping you study!")

bot = AutoShardedClient(intents=Intents.new(
                        guilds=True,
                        direct_messages=True
                        ), sync_interactions=True, activity=activity,
                        total_shards=cfg["Settings"]["shard-count"])

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
