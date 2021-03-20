import discord
from discord.ext import commands

import gspread
import os
import asyncio
import random
from urllib.parse import urlparse

from utils.utilities import textToEmoji, emojiToText
from db import collection

REACTIONS = "abcdefghijklmnopqrstuvwxyz"


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
    async def quiz(self, ctx: commands.Context, *, sheet: str):
        '''
        Begins a singleplayer quiz, given a Studybot-compatible spreadsheet.
        Provide a valid Studybot sheet URL or the name of a Bound spreadsheet.
        '''
        if document := collection("bindings").find_one({"name": sheet}):
            url = document["URL"]
        else:
            url = sheet

        try:
            sheet: gspread.Spreadsheet = self.gc.open_by_url(url)
        except gspread.NoValidUrlKeyFound:
            await ctx.send("Sheet not found. Check that your sheet is shared with **anyone with link**.")
            return


        await ctx.send(f"Starting quiz for `{sheet.title}`...")

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers

        random.shuffle(questions)

        await listen_quiz(ctx, questions)

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

    @commands.command()
    async def bind(self, ctx: commands.Context, url: str, *, name: str):
        '''
        Binds a given spreadsheet to this server or DM to a custom name.
        '''
        locale = ctx.guild.id if ctx.guild else ctx.author.id

        if not collection("bindings").find_one(
                {"locale": locale, "name": name}):
            # Validate URL
            try:
                result = urlparse(url)
                assert all([result.scheme, result.netloc])
            except ValueError:
                await ctx.send("Invalid URL provided.")
                return

            collection("bindings").insert_one(
                {"locale": locale,
                 "name": name,
                 "URL": url,
                 "user": ctx.author.id})

            await ctx.message.add_reaction("👍")

            if ctx.guild:
                await ctx.send(
                    f"Sheet successfully bound to server `{ctx.guild.name}` with name `{name}`.")
            else:
                await ctx.send(
                    f"Sheet successfully bound to DM with name `{name}`.")

        else:
            await ctx.send(
                f"A sheet with name `{name}` already exists in this locale! Try another one.")

    @commands.command()
    async def unbind(self, ctx: commands.Context, *, name: str):
        '''
        Unbinds the spreadsheet with the specified name, if you own it.
        '''
        locale = ctx.guild.id if ctx.guild else ctx.author.id

        if document := collection("bindings").find_one(
                {"locale": locale, "name": name}):

            if document["user"] == ctx.author.id:
                collection("bindings").delete_one({"locale": locale, "name": name})
                await ctx.message.add_reaction("👍")

                if ctx.guild:
                    await ctx.send(
                        f"Sheet with name `{name}` successfully unbound from server `{ctx.guild.name}`.")
                else:
                    await ctx.send(
                        f"Sheet with name `{name}` successfully unbound from this DM.")
            else:
                await ctx.send(f"You are not the owner of sheet `{name}`!")

        else:
            await ctx.send(
                f"A sheet with name `{name}` was not found in this locale.")

    @commands.command()
    async def sheets(self, ctx: commands.Context):
        '''
        Lists all bound sheets on the server.
        '''
        locale = ctx.guild.id if ctx.guild else ctx.author.id

        e = discord.Embed(title=f"All bound sheets in {ctx.guild.name}")

        for document in collection("bindings").find({"locale": locale}):
            e.add_field(name=document["name"], value=f"[Link to Sheet]({document['URL']})")

        await ctx.send(embed=e)


async def listen_quiz(ctx: commands.Context, questions):
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
                payload = await ctx.bot.wait_for(
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

