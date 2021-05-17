import discord
from discord.ext import commands

import gspread
import os
import asyncio
import random
from urllib.parse import urlparse

from utils.utilities import textToEmoji, emojiToText, locale
from db import collection, Airtable
from .utils import IB

from client import bot_prefix

REACTIONS = "abcdefghijklmnopqrstuvwxyz"


def sheet_name(sheet: str) -> str:
    '''
    Transforms a name into a cleaned name for storage
    (At the moment, just makes it lowercase)
    '''
    return sheet.lower()


class Quiz(commands.Cog):
    '''
    Run multiple-choice or flashcard quiz sessions using your own question banks!
    Coming soon: question banks from the web.
    '''
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.airtable: Airtable = Airtable()

        with open("temp.json", "w") as f:
            f.write(os.environ.get("SHEETS"))
        self.gc = gspread.service_account(filename="temp.json")
        os.remove("temp.json")

    @commands.command(hidden=True)
    async def testsheet(self, ctx: commands.Context, url: str):
        '''
        Pulls raw data from spreadsheet for debugging your sheet
        '''
        wks = self.gc.open_by_url(url).get_worksheet(0)
        await ctx.send(wks.get_all_values())

    @commands.command(enabled=False)
    @commands.max_concurrency(100)
    async def IB(self, ctx: commands.Context, url: str = "https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/46-dp-physics/questions/105764.html"):
        '''
        Displays a MCQ from the IB questionbank.
        e.g. `-IB https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/46-dp-physics/questions/105764.html`
        '''
        try:
            question = await IB(url)

            if type(question) == str:
                await ctx.send(f"Question Type is: {question}, which is not supported right now.")
            else:
                await listen_quiz(ctx, [question])
        except Exception:
            await ctx.send("Could not scrape the URL provided.")

    @commands.command()
    @commands.max_concurrency(100)
    async def quiz(self, ctx: commands.Context, *, sheet: str = None):
        '''
        Begins a singleplayer quiz, given a Studybot-compatible spreadsheet.
        Provide a valid Studybot sheet URL or the name of a Bound spreadsheet.
        Create a sheet using `-template`.
        '''
        if not sheet:
            await ctx.send("Please provide a Sheets URL or a valid bound sheet name.\nFor example, `-quiz https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0`\n\nCreate a quiz spreadsheet by running `-template` and following the instructions")
            return

        if document := collection("bindings").find_one({"name_lower": sheet_name(sheet), "locale": locale(ctx)}):
            # Search mongoDB
            url = document["URL"]
        elif record := await self.airtable.find_sheet(sheet):
            # Search airtable
            url = record["fields"]["Link to Sheet"]
        else:
            # Just URL
            url = sheet

        try:
            sheet: gspread.Spreadsheet = self.gc.open_by_url(url)
            title = sheet.title
        except gspread.NoValidUrlKeyFound:
            await ctx.send("Sheet not found. Please check that your sheet exists and is shared with **anyone with link**.")
            return
        except gspread.exceptions.APIError:
            await ctx.send("The sheet you linked is not shared publicly. Please check that your sheet is shared with **anyone with link**.")
            return

        await ctx.send(f"Starting quiz for `{title}`...")

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
        https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0/copy

        **Make a copy of this spreadsheet, and add your own questions!
          Don't forget to set the sheet to `anyone with link can view`**
        ''')

    @commands.command()
    async def bind(self, ctx: commands.Context, url: str = None, *, name: str = None):
        '''
        Binds a given spreadsheet to this server or DM to a custom name.
        e.g. `-bind https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0 Fun Trivia` 
        '''
        if not url or not name:
            await ctx.send("Please provide a Sheets URL or a valid bound sheet name.\nFor example, `-bind https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0 Fun Trivia`\n\nCreate a quiz spreadsheet by running `-template` and following the instructions")
            return

        try:
            admin = await commands.has_guild_permissions(administrator=True).predicate(ctx)
        except commands.errors.MissingPermissions:
            # Checks to make sure that the user has admins privs on the server
            if ((settings := collection("settings").find_one(locale(ctx))) and settings["admin-bind"]) or not collection("settings").find_one(locale(ctx)):
                await ctx.send("Sorry, you need to have the **Administrator** permission to bind sheets in this server.")
                return
        except commands.errors.NoPrivateMessage:
            pass

        if not collection("bindings").find_one(
                {"locale": locale(ctx), "name_lower": sheet_name(name)}):
            # Validate URL
            try:
                result = urlparse(url)
                assert all([result.scheme, result.netloc])
            except ValueError:
                await ctx.send("Invalid URL provided.")
                return

            collection("bindings").insert_one(
                {"locale": locale(ctx),
                 "name": name,
                 "name_lower": sheet_name(name),
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
                f"A sheet with name `{name}` already exists in this locale (names are case insensitive)! Try another one.")

    @commands.command()
    async def unbind(self, ctx: commands.Context, *, name: str = None):
        '''
        Unbinds the spreadsheet with the specified name, if you own it.
        e.g. `-unbind Fun Trivia` 
        '''
        if not name:
            await ctx.send("Please provide the name a of a bound sheet you own. e.g. `-unbind Fun Trivia`")
            return

        if document := collection("bindings").find_one(
                {"locale": locale(ctx), "name_lower": sheet_name(name)}):

            if document["user"] == ctx.author.id:
                collection("bindings").delete_one({"locale": locale(ctx), "name_lower": sheet_name(name)})
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
        To bind a sheet, use the `-bind` command.
        '''

        if ctx.guild:
            e = discord.Embed(title=f"All bound sheets in {ctx.guild.name}")
        else:
            e = discord.Embed(title=f"All bound sheets in this DM")

        for document in collection("bindings").find({"locale": locale(ctx)}):
            e.add_field(name=document["name"], value=f"[Link to Sheet]({document['URL']})")

        await ctx.send(embed=e)

    @commands.command()
    async def explore(self, ctx: commands.Context):
        '''
        Lists premade sheets for you to use in your quizzes!
        '''
        e = discord.Embed()

        e.description = "[See the full list here](https://www.studybot.ca/explore.html)"

        for record in await self.airtable.sheets:
            record = record["fields"]
            e.add_field(name=record["Sheet Name"],
                        value=f"{record['Description']}\nBy: {record['Creator Discord Tag']}",
                        inline=False)

        e.set_footer(text=f"To start a quiz using one of these sheets, use [{await bot_prefix(self.bot, ctx.message)}quiz <sheet name>]", icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=e, content=
            f"Here are the Studybot official curated sheets, ready for you to use in the `{await bot_prefix(self.bot, ctx.message)}quiz` command!")


# Helper coros
async def sweep_reactions(
        ctx: commands.Context,
        message: discord.Message) -> \
        discord.RawReactionActionEvent:
    '''
    Sweep all reactions on a message
    '''
    while 1:
        reaction: discord.Reaction
        for reaction in message.reactions:
            # Scan all reactions
            user: discord.User
            async for user in reaction.users():
                # Scan all users in reaction
                if user.id == ctx.author.id:
                    # Pick first emoji which has author's reaction
                    return discord.RawReactionActionEvent(
                        {"message_id": message.id,
                            "channel_id": message.channel.id,
                            "user_id": user.id}, reaction.emoji, None)
    await asyncio.sleep(1)


async def send_result(mcq: bool,
                      ctx: commands.Context,
                      message: discord.Message,
                      emoji: discord.Emoji,
                      options: list,
                      correct_index: int) -> None:
    '''
    Sends the result of a quiz given the user's response
    '''
    if mcq:
        # Determine whether MCQ answer is correct or not
        correct_reaction: discord.Reaction = message.reactions[correct_index]

        ctx.current_mcq += 1  # Add 1 to total MCQ
        if str(correct_reaction.emoji) == str(emoji):
            ctx.current_score += 1  # Add 1 to current score
            e = discord.Embed(
                colour=discord.Color.green(), title="Correct",
                description=str(correct_reaction) + " " + options[correct_index])
        else:
            e = discord.Embed(
                colour=discord.Color.red(), title="Incorrect",
                description=str(correct_reaction) + " " + options[correct_index])

        e.set_footer(text=f"You Answered: {emojiToText(str(emoji)).upper()}\nCurrent Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%")

    else:
        # Show flashcard answer
        e = discord.Embed(
            colour=discord.Color.blue())

        answers = "\n".join(options)

        if options and len(answers) < 256:
            e.title = answers
        elif options:
            e.description = answers
        else:
            e.title = "(No Answer Found)"

    await ctx.send(embed=e)


async def listen_quiz(ctx: commands.Context, questions: list):
    cont = True

    ctx.current_score = 0
    ctx.current_mcq = 0

    while cont and questions:
        # Verify list is not empty

        current_question = questions.pop(0)
        prompt = current_question[0]

        if not prompt:
            continue
            # Move to next question since this one is empty

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

            correct_index: int = ord(current_question[-1][0].lower()) - 97

            for i in range(len(options)):
                desc_text += f"{textToEmoji(REACTIONS[i])}: {options[i]}\n"

            e.description = desc_text  # Add the MCQ options to the description
            # Description now has question text (maybe) + mcq questions

            e.set_author(
                name="React with the correct answer",
                icon_url=ctx.author.avatar_url)
        else:
            correct_index: int = 0  # Give it a default value so as to not raise an error
            e.set_author(
                name="React with ✅ to see the answer",
                icon_url=ctx.author.avatar_url)

        msg = await ctx.send(embed=e)  # Message that bot sends

        if mcq:
            for i in range(len(options)):
                await msg.add_reaction(textToEmoji(REACTIONS[i]))
        else:
            await msg.add_reaction("✅")
        await msg.add_reaction("🛑")

        # LISTEN for reactions
        def check(payload):
            return payload.message_id == msg.id and payload.user_id == ctx.author.id

        message = await msg.channel.fetch_message(msg.id)

        try:
            pending_tasks = [
                ctx.bot.wait_for("raw_reaction_add", timeout=120, check=check),
                sweep_reactions(ctx, message)
            ]

            # Process tasks
            done_tasks, pending_tasks = await asyncio.wait(
                pending_tasks, return_when=asyncio.FIRST_COMPLETED)

            for task in pending_tasks:
                task.cancel()

            for task in done_tasks:
                payload: discord.RawReactionActionEvent = await task
            # Extract payload from tasks

            if str(payload.emoji) == "🛑":
                finalscore = f"Final Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%" if ctx.current_mcq else None

                await ctx.send(
                    "Quiz Terminated. Enter a new link to start again!" + (
                        ("\n"+finalscore) if finalscore else ""))
                return

            await send_result(
                mcq, ctx, message, payload.emoji, options, correct_index)

        except asyncio.TimeoutError:
            cont = False
            await msg.edit(
                content="**Quiz timed out after 120 seconds of inactivity.**")
            return

    if not questions:
        finalscore = f"Final Score: {ctx.current_score}/{ctx.current_mcq} = {round(ctx.current_score/ctx.current_mcq*100)}%" if ctx.current_mcq else None
        await ctx.send(
            "Question deck has been exhausted. Enter a new link to start again!" + (("\n"+finalscore) if finalscore else ""))
        return
