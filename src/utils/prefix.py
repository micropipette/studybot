from db import collection
import discord
from discord.ext import commands
from config import cfg

# Map prefixes
async def bot_prefix(bot: commands.AutoShardedBot, message: discord.Message):
    '''
    Returns bot prefix for a specific locale
    '''
    locale = message.guild.id if message.guild else message.author.id

    if settings := collection("settings").find_one(locale):
        return commands.when_mentioned_or(settings["prefix"])(bot, message)
    else:
        return commands.when_mentioned_or(
            cfg["Settings"]["prefix"].strip("\""))(bot, message)