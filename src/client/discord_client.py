import discord
from discord.ext import commands
from config import cfg
from utils.logger import logger
from db import collection


# Map prefixes
async def bot_prefix(bot: commands.Bot, message: discord.Message):
    '''
    Returns bot prefix for a specific locale
    '''
    locale = message.guild.id if message.guild else message.author.id

    if settings := collection("settings").find_one({"locale": locale}):
        return commands.when_mentioned_or(settings["prefix"])
    else:
        return commands.when_mentioned_or(
            cfg["Settings"]["prefix"].strip("\""))

intents = discord.Intents.default()

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
