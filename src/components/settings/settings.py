import discord
from discord.ext import commands
from utils.utilities import locale
from db import collection


def default_settings(ctx):
    '''
    Returns default settings document for servers
    '''
    return {"_id": locale(ctx), "prefix": "-", "admin-bind": True}


class Settings(commands.Cog):
    '''
    Set the configuration for the bot on the server
    '''
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command()
    @commands.check(commands.has_guild_permissions(administrator=True))
    async def prefix(self, ctx: commands.Context, prefix: str = None):
        '''
        Sets the prefix for the bot in the server, or sets it if no prefix is provided
        '''
        if prefix is None:
            await ctx.send(f"Current Prefix is: `{(await self.bot.get_prefix(ctx.message))[-1]}`")

        else:
            if settings := collection("settings").find_one(
                    {"locale": locale(ctx)}):
                collection("settings").update_one(
                    {"locale": locale(ctx)}, {"$set": {"prefix": prefix}})
            else:
                # Need a new setings doc
                settings = default_settings(ctx)
                settings["prefix"] = prefix
                collection("settings").insert_one(settings)
            await ctx.message.add_reaction("👍")

    @commands.command()
    @commands.check(commands.has_guild_permissions(administrator=True))
    async def allowuserbind(self, ctx: commands.Context, allow: bool = True):
        '''
        allows users to bind or not bind sheets to the server
        '''
        if settings := collection("settings").find_one(
                {"locale": locale(ctx)}):
            collection("settings").update_one(
                {"locale": locale(ctx)}, {"$set": {"admin-bind": not allow}})
        else:
            # Need a new setings doc
            settings = default_settings(ctx)
            settings["admin-bind"] = not allow
            collection("settings").insert_one(settings)

        if allow:
            await ctx.send("All users are now allowed to bind sheets.")
        else:
            await ctx.send("Only **Administrators** are now allowed to bind sheets.")
