import discord
from discord.ext import commands

class Editor(commands.Cog):
    def __init__(self, bot):
        self.bot: commands.Bot = bot
    
    async def create(self, ctx: commands.Context, *, name: str):
        '''
        Create your own quiz from within discord
        '''
        await ctx.send(f"Initializing editor for question bank `{name}`...")

        await self.bot.wait_for()
