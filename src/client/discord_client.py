import discord
from discord.ext import commands
from config import cfg
from utils.logger import logger
from db import collection
import os


# Map prefixes
async def bot_prefix(bot: commands.Bot, message: discord.Message):
    '''
    Returns bot prefix for a specific locale
    '''
    locale = message.guild.id if message.guild else message.author.id

    if settings := collection("settings").find_one(locale):
        return commands.when_mentioned_or(settings["prefix"])(bot, message)
    else:
        return commands.when_mentioned_or(
            cfg["Settings"]["prefix"].strip("\""))(bot, message)

intents = discord.Intents(guilds=True, messages=True, reactions=True)

client = commands.Bot(
    command_prefix=bot_prefix,
    case_insensitive=True,
    help_command=commands.MinimalHelpCommand(),
    intents=intents,
    status=discord.Status.online,
    activity=discord.Game(cfg["Settings"]["Status"]))

help = client.get_command("help")
help.hidden = True


@client.event
async def on_error(event, *args, **kwargs):
    if type(event) == discord.HTTPException:
        os.system("kill 1")  # hard restart on 429

    try:
        raise event
    except Exception:
        logger.exception(event)


@client.event
async def on_command_error(ctx: commands.Context, exception):
    # When a command fails to execute

    if type(exception) == commands.CommandNotFound:
        await ctx.send(exception)
    else:
        logger.exception("Command Error", exc_info=exception)
        await ctx.send(f"An unexpected error occurred. If this problem persists, please let us know in the **Studyboy Official Server!**```{exception}```")
