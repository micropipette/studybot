import discord
from discord.ext import commands

import gspread
import os
import asyncio
import random

REACTIONS = "abcdefghijklmnopqrstuvwxyz"


def textToEmoji(s) -> str:
    '''
    Converts text to equivalent emoji
    '''
    lookupTable = {
                "a": "\N{REGIONAL INDICATOR SYMBOL LETTER A}",
                "b": "\N{REGIONAL INDICATOR SYMBOL LETTER B}",
                "c": "\N{REGIONAL INDICATOR SYMBOL LETTER C}",
                "d": "\N{REGIONAL INDICATOR SYMBOL LETTER D}",
                "e": "\N{REGIONAL INDICATOR SYMBOL LETTER E}",
                "f": "\N{REGIONAL INDICATOR SYMBOL LETTER F}",
                "g": "\N{REGIONAL INDICATOR SYMBOL LETTER G}",
                "h": "\N{REGIONAL INDICATOR SYMBOL LETTER H}",
                "i": "\N{REGIONAL INDICATOR SYMBOL LETTER I}",
                "j": "\N{REGIONAL INDICATOR SYMBOL LETTER J}",
                "k": "\N{REGIONAL INDICATOR SYMBOL LETTER K}",
                "l": "\N{REGIONAL INDICATOR SYMBOL LETTER L}",
                "m": "\N{REGIONAL INDICATOR SYMBOL LETTER M}",
                "n": "\N{REGIONAL INDICATOR SYMBOL LETTER N}",
                "o": "\N{REGIONAL INDICATOR SYMBOL LETTER O}",
                "p": "\N{REGIONAL INDICATOR SYMBOL LETTER P}",
                "q": "\N{REGIONAL INDICATOR SYMBOL LETTER Q}",
                "r": "\N{REGIONAL INDICATOR SYMBOL LETTER R}",
                "s": "\N{REGIONAL INDICATOR SYMBOL LETTER S}",
                "t": "\N{REGIONAL INDICATOR SYMBOL LETTER T}",
                "u": "\N{REGIONAL INDICATOR SYMBOL LETTER U}",
                "v": "\N{REGIONAL INDICATOR SYMBOL LETTER V}",
                "w": "\N{REGIONAL INDICATOR SYMBOL LETTER W}",
                "x": "\N{REGIONAL INDICATOR SYMBOL LETTER X}",
                "y": "\N{REGIONAL INDICATOR SYMBOL LETTER Y}",
                "z": "\N{REGIONAL INDICATOR SYMBOL LETTER Z}"}
    return lookupTable[s]


def emojiToText(s) -> str:
    '''
    Converts emoji to closest real text representation (lowercase output)
    Note: Will strip spaces.
    '''
    lookupTable = {
        u"\U0001F1E6": "a",
        u"\U0001F1E7": "b",
        u"\U0001F1E8": "c",
        u"\U0001F1E9": "d",
        u"\U0001F1EA": "e",
        u"\U0001F1EB": "f",
        u"\U0001F1EC": "g",
        u"\U0001F1ED": "h",
        u"\U0001F1EE": "i",
        u"\U0001F1EF": "j",
        u"\U0001F1F0": "k",
        u"\U0001F1F1": "l",
        u"\U0001F1F2": "m",
        u"\U0001F1F3": "n",
        u"\U0001F1F4": "o",
        u"\U0001F1F5": "p",
        u"\U0001F1F6": "q",
        u"\U0001F1F7": "r",
        u"\U0001F1F8": "s",
        u"\U0001F1F9": "t",
        u"\U0001F1FA": "u",
        u"\U0001F1FB": "v",
        u"\U0001F1FC": "w",
        u"\U0001F1FD": "x",
        u"\U0001F1FE": "y",
        u"\U0001F1FF": "z",
        "0️⃣": 0,
        "1️⃣": 1,
        "2️⃣": 2,
        "3️⃣": 3,
        "4️⃣": 4,
        "5️⃣": 5,
        "6️⃣": 6,
        "7️⃣": 7,
        "8️⃣": 8,
        "9️⃣": 9}

    newS = ''

    i = 0

    while i < len(s):
        if s[i] in lookupTable:
            newS += lookupTable[s[i]]
            i += 1
        else:
            newS += s[i]
        i += 1
    return newS


class Quiz(commands.Cog):
    '''
    Run multiple-choice or flashcard quiz sessions using your own question banks!
    Coming soon: question banks from the web.
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
        Begins a singleplayer quiz, given a Studybot-compatible spreadsheet.
        Run [-template] to get a link to a template spreadsheet.
        '''
        try:
            sheet: gspread.Spreadsheet = self.gc.open_by_url(url)
        except gspread.NoValidUrlKeyFound:
            await ctx.send("Sheet not found. Check that your sheet is shared with **anyone with link**.")
            return

        await ctx.send(f"Starting quiz for `{sheet.title}`...")

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers

        random.shuffle(questions)

        await self.listen_quiz(ctx, questions)

    async def listen_quiz(self, ctx: commands.Context, questions):
        cont = True

        while cont and questions:
            # Verify list is not empty

            current_question = questions.pop(0)
            prompt = current_question[0]
            image_url = current_question[1]
            mcq = False

            e = discord.Embed(color=discord.Color.blue())

            desc_text = ""

            if len(prompt) < 252:
                e.title = f"**{prompt}**"
            else:
                desc_text = f"**{prompt}**\n"

            e.set_footer(
                    text=f"{ctx.author.display_name}, react to this post with 🛑 to stop the quiz.")

            options = [
                op.strip("\n") for op in current_question[
                    2:-1] if op]  # Take only non blank entries

            if image_url:
                e.set_image(url=image_url)

            if current_question[-1]:
                # Multiple choice
                mcq = True
                correct_index = ord(current_question[-1][0].lower()) - 97

                for i in range(len(options)):
                    desc_text += f"{textToEmoji(REACTIONS[i])}: {options[i]}\n"

                e.description = desc_text

                e.set_author(
                    name="React with the correct answer",
                    icon_url=ctx.author.avatar_url)
            else:
                e.set_author(
                    name="React with ✅ to see the answer",
                    icon_url=ctx.author.avatar_url)

            msg = await ctx.send(embed=e)

            if mcq:
                for i in range(len(options)):
                    await msg.add_reaction(textToEmoji(REACTIONS[i]))
            else:
                await msg.add_reaction("✅")
            await msg.add_reaction("🛑")

            def check(payload):
                return payload.message_id == msg.id and payload.user_id == ctx.author.id

            message = await msg.channel.fetch_message(msg.id)

            async def send_result(emoji):
                '''
                Sends the result of a quiz given the user's response
                '''
                if mcq:
                    correct_reaction = message.reactions[correct_index]

                    if ctx.author in (await correct_reaction.users().flatten()):
                        e = discord.Embed(
                            colour=discord.Color.green(), title="Correct",
                            description=str(correct_reaction) + " " + options[correct_index])
                    else:
                        e = discord.Embed(
                            colour=discord.Color.red(), title="Incorrect",
                            description=str(correct_reaction) + " " + options[correct_index])
                    e.set_footer(text=f"You Answered: {emojiToText(str(emoji)).upper()}")
                else:
                    e = discord.Embed(
                        colour=discord.Color.blue())

                    if len(options[0]) < 256:
                        e.title = options[0]
                    else:
                        e.description = options[0]

                await ctx.send(embed=e)

            try:
                # Refresh quiz to see if anyone has responded even before the listener is ready
                listen = True
                for reaction in message.reactions:
                    if reaction.count > 1 and ctx.author in (await reaction.users().flatten()):
                        listen = False
                        await send_result(reaction.emoji)

                if listen:
                    payload = await self.bot.wait_for(
                        "raw_reaction_add", timeout=120, check=check)

                    if payload.emoji.name == "🛑":
                        await ctx.send(
                            "Quiz Terminated. Enter a new link to start again!")
                        raise asyncio.TimeoutError

                    await send_result(payload.emoji)

            except asyncio.TimeoutError:
                cont = False

        if not questions:
            await ctx.send(
                "Question deck has been exhausted. Enter a new link to start again!")

    @commands.command()
    async def template(self, ctx: commands.Context):
        '''
        Gets the link for the template spreadsheet.

        Make a copy of this spreadsheet, and fill with your own questions!
        '''
        await ctx.send('''Template spreadsheet:
        https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0/edit?usp=sharing

        **Make a copy of this spreadsheet, and edit with your own questions!
          Don't forget to set the sheet to `anyone with link can view`**
        ''')
