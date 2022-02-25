import dotenv
import os
from logger import log

from dis_snek.client import Snake
from dis_snek.models.enums import Intents
from dis_snek.models.listener import listen
from dis_snek.models.context import Context, InteractionContext, MessageContext
from dis_snek.models.discord_objects.activity import Activity
import topgg
from db import mongo_startup

from dis_snek.tasks.task import Task
from dis_snek.tasks.triggers import IntervalTrigger
import argparse

dotenv.load_dotenv()  # Load .env file, prior to components loading

parser = argparse.ArgumentParser()
parser.add_argument("shard_count", type=int, help="Number of shards in total")
parser.add_argument("shard_id", type=int, help="id of shard to spawn")
args = parser.parse_args()

mongo_startup()

class CustomSnake(Snake):
    async def on_command_error(self, ctx: Context,
                               error: Exception):
        log.exception(msg=error, exc_info=error)
        if type(ctx) == InteractionContext and not ctx.responded:
            await ctx.send("Something went wrong while executing the command.\n"
                           f"Error: `{error}`", ephemeral=True)
        elif type(ctx) == MessageContext:
            await ctx.send("Something went wrong while executing the command.\n"
                           f"Error: `{error}`", reply_to = ctx.message)

activity = Activity.create(name="helping you study!")

bot = CustomSnake(intents=Intents.new(
                        guilds=True,
                        guild_messages=True,
                        direct_messages=True
                    ), sync_interactions=True, activity=activity,
                  total_shards=args.shard_count, shard_id=args.shard_id)

bot.topgg = topgg.DBLClient(bot, os.environ.get("TOPGG"))
# top.gg client to push server count

@Task.create(IntervalTrigger(minutes=30))
async def update_guild_count():
    try:
        await bot.topgg.post_guild_count(
            guild_count=len(bot.guilds),
            shard_count=args.shard_count,
            shard_id=args.shard_id)
        log.info(f"Updated guild count to {len(bot.guilds)}")
    except BaseException:
        log.exception(msg="Failed to update guild count")

@listen()
async def on_ready():
    log.info(f"{bot.user.username} is online. Shard ID = {args.shard_id}/{args.shard_count}")
    update_guild_count.start()
    
# Locate and load all modules under "modules"
for module in os.listdir("./modules"):
    if module.endswith(".py") and not module.startswith("_"):
        try:
            bot.grow_scale(f"modules.{module[:-3]}")
        except Exception as e:
            log.exception(f"Failed to load extension {module}")
        

bot.start(os.environ.get("TOKEN"))
