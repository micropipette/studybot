import discord
from discord.ext import commands
from config import version
import sys
import os

from utils.utilities import get_uptime


class Testing(commands.Cog):
    '''
    Commands for testing the bot.
    '''
    def __init__(self, bot):
        self.bot: commands.Bot = bot

    @commands.command(hidden=True)
    async def status(self, ctx: commands.Context):
        '''
        Shows the current status of the bot on the remote host.
        '''
        await ctx.send(f"**Uptime**: {round(get_uptime(), 1)}s\n"
                       f"**Version**: {version}\n"
                       f"Currently Connected to **{len(self.bot.guilds)}** server(s)\n"
                       f"**API Latency**: {round(self.bot.latency, 4)}s\n"
                       f"Running discord.py version {discord.__version__}")

    @commands.command(hidden=True)
    @commands.is_owner()
    async def restart(self, ctx: commands.Context):
        '''
        Restarts the bot on the remote host. Must be bot owner.
        '''
        await ctx.send("Restarting...")
        await self.bot.change_presence(status=discord.Status.offline)
        await self.bot.logout()
        sys.exit(0)

    @commands.command(hidden=True)
    @commands.is_owner()
    async def hardrestart(self, ctx: commands.Context):
        '''
        Hard restarts the bot on replit
        '''
        await ctx.send("Hard Restarting...")
        os.system("kill 1")
