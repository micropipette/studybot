import discord
from discord.ext import commands

import gspread
import os
import asyncio

REACTIONS = "123456789abcdefghijklmnopqrstuvwxyz"


def textToEmoji(s) -> str:
    '''
    Converts text to equivalent emoji
    '''
    lookupTable = {
        "a": u"\U0001F1E6",
        "b": u"\U0001F1E7",
        "c": u"\U0001F1E8",
        "d": u"\U0001F1E9",
        "e": u"\U0001F1EA",
        "f": u"\U0001F1EB",
        "g": u"\U0001F1EC",
        "h": u"\U0001F1ED",
        "i": u"\U0001F1EE",
        "j": u"\U0001F1EF",
        "k": u"\U0001F1F0",
        "l": u"\U0001F1F1",
        "m": u"\U0001F1F2",
        "n": u"\U0001F1F3",
        "o": u"\U0001F1F4",
        "p": u"\U0001F1F5",
        "q": u"\U0001F1F6",
        "r": u"\U0001F1F7",
        "s": u"\U0001F1F8",
        "t": u"\U0001F1F9",
        "u": u"\U0001F1FA",
        "v": u"\U0001F1FB",
        "w": u"\U0001F1FC",
        "x": u"\U0001F1FD",
        "y": u"\U0001F1FE",
        "z": u"\U0001F1FF"}
    s = s.lower()

    newS = ''
    for c in s:
        if c in lookupTable:
            newS += lookupTable[c] + " "
        elif c in "0123456789":
            newS += {0: "0️⃣", 1: "1️⃣", 2: "2️⃣", 3: "3️⃣", 4: "4️⃣",
                     5: "5️⃣", 6: "6️⃣", 7: "7️⃣", 8: "8️⃣", 9: "9️⃣"}[int(c)]
        else:
            newS += c
    return newS


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
        '''
        Pulls raw data from spreadsheet for debugging
        '''

        wks = self.gc.open_by_url(url).get_worksheet(0)

        await ctx.send(wks.get_all_values())

    @commands.command()
    @commands.max_concurrency(20)
    async def quiz(self, ctx: commands.Context, url: str):
        '''
        Multiple choice questions.
        '''
        wks = self.gc.open_by_url(url).get_worksheet(0)

        questions = wks.get_all_values()

        await self.listen_quiz(ctx, questions)

    async def listen_quiz(self, ctx: commands.Context, questions):
        cont = True

        while cont and questions:
            # Verify list is not empty

            current_question = questions.pop(0)

            prompt = current_question[0]

            options = current_question[1:-1]

            correct_index = int(current_question[-1]) - 1

            e = discord.Embed(title=f"**{prompt}**", color=discord.Color.blue())
            e.set_author(
                name=f"{ctx.author.display_name}, react to this post with 🛑 to stop the quiz.",
                icon_url=ctx.author.avatar_url)

            for i in range(len(options)):
                e.add_field(
                    name=textToEmoji(REACTIONS[i]),
                    value=options[i],
                    inline=False)

            e.set_footer(
                text="Studybot Quiz")

            msg = await ctx.send(embed=e)

            for i in range(len(options)):
                await msg.add_reaction(textToEmoji(REACTIONS[i]))
            await msg.add_reaction("🛑")

            def check(payload):
                return payload.message_id == msg.id and not self.bot.get_user(payload.user_id).bot

            try:
                payload = await self.bot.wait_for(
                    "raw_reaction_add", timeout=120, check=check)

                user = self.bot.get_user(payload.user_id)
                message = await msg.channel.fetch_message(payload.message_id)

                if payload.emoji.name == "🛑" and user.id == ctx.author.id:
                    await ctx.send("POLL TERMINATED")
                    raise asyncio.TimeoutError

                correct_reaction = message.reactions[correct_index]

                if user in (await correct_reaction.users().flatten()):
                    await ctx.send("CORRECT")

                else:
                    await ctx.send("INCORRECT")

            except asyncio.TimeoutError:
                cont = False
        if not questions:
            await ctx.send("QUESTION DECK EXHAUSTED")
