import discord
from discord.ext import commands
from config import cfg
from pretty_help import PrettyHelp
from utils.logger import logger

# Map prefixes
if cfg["Settings"]["secondary-prefix"]:
    prefixes = commands.when_mentioned_or(
        cfg["Settings"]["prefix"].strip("\""),
        cfg["Settings"]["secondary-prefix"].strip("\""))
else:
    prefixes = commands.when_mentioned_or(
        cfg["Settings"]["prefix"].strip("\""))

intents = discord.Intents.all()

client = commands.Bot(
    command_prefix=prefixes,
    case_insensitive=True,
    help_command=PrettyHelp(
        no_category="Help Command",
        color=discord.Color.blue(),
        sort_commands=False),
    intents=intents,
    status=discord.Status.online,
    activity=discord.Game(cfg["Settings"]["Status"]))


@client.event
async def on_error(event, *args, **kwargs):
    try:
        raise event
    except Exception:
        logger.exception(event)


@client.event
async def on_command_error(ctx: commands.Context, exception):
    # When a command fails to execute
    logger.exception("Command Error", exc_info=exception)
    with open("studybot.log", "rb") as f:
        await ctx.send(
            f"Error: {exception}\n\n**Attached is a log of what went wrong. Please send this to `itchono#3597`**",
            reference=ctx.message,
            file=discord.File(f, filename="studybot_log.txt"))
