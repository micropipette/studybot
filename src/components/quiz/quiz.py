import discord
from discord.ext import commands
from discord_slash.context import SlashContext
import gspread
import os
import random
from urllib.parse import urlparse
from utils.utilities import locale
from db import collection, Airtable
from .utils import IB
from .quiz_backend import listen_quiz
from discord_slash import cog_ext, SlashCommandOptionType
from discord_slash.utils.manage_commands import create_option


def sheet_name(sheet: str) -> str:
    '''
    Transforms a name into a cleaned name for storage
    (At the moment, just makes it lowercase)
    '''
    return sheet.lower()


class Quizzes(commands.Cog):
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

    @commands.command(enabled=False)
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

    @cog_ext.cog_slash(name="quiz", description="Begins a singleplayer quiz, given a Studybot-compatible spreadsheet.",
                       options=[create_option(
                           name="sheet",
                           description="name or URL of the sheet",
                           option_type=SlashCommandOptionType.STRING,
                           required=True
                       )
                       ])
    async def slash_quiz(self, ctx: SlashContext, sheet: str=None):

        if not ctx.guild:
            dm_channel = await ctx.author.create_dm()
            ctx.channel_id = dm_channel.id

        await self.quiz(ctx=ctx, sheet=sheet)

    @cog_ext.cog_slash(name="template", description="Gets the link for the template spreadsheet, which you can modify to make your own quizzes!")
    async def slash_template(self, ctx: SlashContext):
        e = discord.Embed()
        e.set_image(url="https://cdn.discordapp.com/attachments/804388848510435370/827998690886418463/ezgif-7-c601e2fb575f.gif")
        await ctx.send(hidden=True,
                       content='''[Template spreadsheet](https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0/copy)
**Make a copy of this spreadsheet, and add your own questions!
Don't forget to set the sheet to `anyone with link can view`**
        ''')

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

        e.set_footer(text=f"To start a quiz using one of these sheets, use [{ctx.prefix}quiz <sheet name>]", icon_url=self.bot.user.avatar_url)

        await ctx.send(embed=e, content=
            f"Here are the Studybot official curated sheets, ready for you to use in the `{ctx.prefix}quiz` command!")
