import discord
from discord.ext import commands

import gspread
import os
import asyncio

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
        Begin a quiz, given a Studybot-compatible spreadsheet.
        Run [-template] to get a link to a template spreadsheet.
        '''
        try:
            sheet: gspread.Spreadsheet = self.gc.open_by_url(url)
        except gspread.SpreadsheetNotFound:
            await ctx.send("Sheet not found. Check that your sheet is shared with **anyone with link**.")

        await ctx.send(f"Starting quiz for `{sheet.title}`...")

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers

        await self.listen_quiz(ctx, questions)

    async def listen_quiz(self, ctx: commands.Context, questions):
        cont = True

        while cont and questions:
            # Verify list is not empty

            current_question = questions.pop(0)
            prompt = current_question[0]
            mcq = False

            e = discord.Embed(color=discord.Color.blue())

            desc_text = ""

            if len(prompt) < 252:
                e.title = f"**{prompt}**"
            else:
                desc_text = f"**{prompt}**\n"

            e.set_author(
                name=f"{ctx.author.display_name}, react to this post with 🛑 to stop the quiz.",
                icon_url=ctx.author.avatar_url)

            options = [
                op for op in current_question[
                    1:-1] if op]  # Take only non blank entries

            if current_question[-1]:
                # Multiple choice
                mcq = True
                correct_index = ord(current_question[-1][0].lower()) - 97

                for i in range(len(options)):
                    desc_text += f"{textToEmoji(REACTIONS[i])}: {options[i]}\n"

                e.description = desc_text

                e.set_footer(
                    text="React with the correct answer")
            else:
                e.set_footer(
                    text="React with ✅ to see the answer")

            msg = await ctx.send(embed=e)

            if mcq:
                for i in range(len(options)):
                    await msg.add_reaction(textToEmoji(REACTIONS[i]))
            else:
                await msg.add_reaction("✅")
            await msg.add_reaction("🛑")

            def check(payload):
                return payload.message_id == msg.id and not self.bot.get_user(
                    payload.user_id).bot

            try:
                payload = await self.bot.wait_for(
                    "raw_reaction_add", timeout=120, check=check)

                user = self.bot.get_user(payload.user_id)
                message = await msg.channel.fetch_message(payload.message_id)

                if payload.emoji.name == "🛑" and user.id == ctx.author.id:
                    await ctx.send(
                        "Quiz Terminated. Enter a new link to start again!")
                    raise asyncio.TimeoutError

                if mcq:
                    correct_reaction = message.reactions[correct_index]

                    if user in (await correct_reaction.users().flatten()):
                        e = discord.Embed(
                            colour=discord.Color.green(), title="Correct",
                            description=str(correct_reaction) + " " + options[correct_index])
                    else:
                        e = discord.Embed(
                            colour=discord.Color.red(), title="Incorrect",
                            description=str(correct_reaction) + " " + options[correct_index])
                else:
                    e = discord.Embed(
                        colour=discord.Color.blue())

                    if len(options[0]) < 256:
                        e.title = options[0]
                    else:
                        e.description = options[0]

                await ctx.send(embed=e)

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
