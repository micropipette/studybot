import discord
from discord.ext import commands

import gspread
import os


class Quiz(commands.Cog):
    '''
    Quiz module
    '''
    def __init__(self, bot):
        self.bot: commands.Bot = bot

        with open("temp.json", "w") as f:
            f.write(os.environ.get("SHEETS"))
        self.gc = gspread.service_account(filename="temp.json")
        os.remove("temp.json")

    @commands.command()
    async def testsheet(self, ctx: commands.Context, url: str):

        wks = self.gc.open_by_url(url).get_worksheet(0)

        await ctx.send(wks.get_all_values())

