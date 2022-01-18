import discord
from discord.ext import commands
import gspread
import os
import random
from urllib.parse import urlparse
from utils.utilities import locale
from db import collection, Airtable
from .quiz_backend import listen_quiz, listen_quiz_mp
from discord_components import Button, ButtonStyle, ActionRow
from utils.button_menu import send_menu_linker

# Slash command stuff
from discord_slash import SlashContext
from discord_slash import cog_ext
from discord_slash.utils import manage_commands


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
        self.bot: commands.AutoShardedBot = bot
        self.airtable: Airtable = Airtable()

        with open("temp.json", "w") as f:
            f.write(os.environ.get("SHEETS"))
        self.gc = gspread.service_account(filename="temp.json")
        os.remove("temp.json")

    # @commands.command(enabled=False)
    # async def IB(self, ctx: commands.Context, url: str = "https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/46-dp-physics/questions/105764.html"):
    #     '''
    #     Displays a MCQ from the IB questionbank.
    #     e.g. `-IB https://www.ibdocuments.com/IB%20QUESTIONBANKS/4.%20Fourth%20Edition/questionbank.ibo.org/en/teachers/00000/questionbanks/46-dp-physics/questions/105764.html`
    #     '''
    #     try:
    #         question = await IB(url)

    #         if type(question) == str:
    #             await ctx.send(f"Question Type is: {question}, which is not supported right now.")
    #         else:
    #             await listen_quiz(ctx, [question])
    #     except Exception:
    #         await ctx.send("Could not scrape the URL provided.")

    @cog_ext.cog_slash(name="quiz",
                       description="Begins a singleplayer quiz from a Studybot sheet.",
                       options=[manage_commands.create_option(
                            name="sheet",
                            description="Sheet URL or name of bound sheet",
                            option_type=3,
                            required=True
                       )])
    async def quiz(self, ctx: SlashContext, sheet: str):
        '''
        Begins a singleplayer quiz from a Studybot sheet.
        Provide a sheet URL or the name of a Bound spreadsheet.
        Create your own sheet using the `template` command.
        '''
        if not sheet:
            await ctx.send(f"Please provide a Sheets URL or a valid bound sheet name.\nFor example, `/quiz https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0`\n\nCreate a quiz spreadsheet by running `/template` and following the instructions")
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
            await ctx.send("Sheet not found. Please check that your sheet exists and is shared with **anyone with link**.", hidden=True)
            return
        except gspread.exceptions.APIError:
            await ctx.send("The sheet you linked is not shared publicly. Please check that your sheet is shared with **anyone with link**.", hidden=True)
            return

        start_embed = discord.Embed(title=f"Starting quiz for `{title}`...", colour=discord.Colour.green())

        start_embed.set_author(icon_url=ctx.author.avatar_url, name=f"Quiz for {ctx.author.display_name}")

        await ctx.send(embed=start_embed)

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers

        random.shuffle(questions)

        await listen_quiz(ctx, questions)

    @cog_ext.cog_slash(name="quizmp",
                       description="Begins a multiplayer quiz from a Studybot sheet.",
                       options=[manage_commands.create_option(
                            name="sheet",
                            description="Sheet URL or name of bound sheet",
                            option_type=3,
                            required=True
                       )])
    async def quizmp(self, ctx: commands.Context, sheet: str):
        '''
        Begins a multiplayer quiz from a Studybot sheet.
        Provide a sheet URL or the name of a Bound spreadsheet.
        Create your own sheet using the `template` command.
        '''
        if not sheet:
            await ctx.send(f"Please provide a Sheets URL or a valid bound sheet name.\nFor example, `/quiz https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0`\n\nCreate a quiz spreadsheet by running `/template` and following the instructions")
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

        start_embed = discord.Embed(title=f"Starting quiz for `{title}`...", colour=discord.Colour.green())

        await ctx.send(embed=start_embed)

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers

        random.shuffle(questions)

        await listen_quiz_mp(ctx, questions)

    @cog_ext.cog_slash(name="template",
                        description="Gets the link for the template spreadsheet.")
    async def template(self, ctx: SlashContext):
        e = discord.Embed(title="Using the template")
        e.set_image(url="https://cdn.discordapp.com/attachments/804388848510435370/827998690886418463/ezgif-7-c601e2fb575f.gif")

        components = [ActionRow(Button(label="Template spreadsheet", style=ButtonStyle.URL,
                      url="https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0/copy"),
                      Button(label="Tutorial Video", style=ButtonStyle.URL,
                      url="https://youtu.be/cdv8aSUOyMg")).to_dict()]
        await ctx.send(embed=e,
        content="**Make a copy of this spreadsheet, and add your own questions!\nDon't forget to set the sheet to `anyone with link can view`**",
        components=components, hidden=True)


    @cog_ext.cog_slash(name="bind",
                       description="Binds a given spreadsheet to this context under a custom name.",
                       options=[manage_commands.create_option(
                            name="url",
                            description="Sheet URL",
                            option_type=3,
                            required=True),
                            manage_commands.create_option(
                            name="name",
                            description="Name of Bound Sheet",
                            option_type=3,
                            required=True)])
    async def bind(self, ctx: SlashContext, url: str, name: str):
        if not url or not name:
            await ctx.send(f"Please provide a Sheets URL or a valid bound sheet name.\nFor example, `/bind https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0 Fun Trivia`\n\nCreate a quiz spreadsheet by running `/template` and following the instructions")
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
        '''
        if not name:
            await ctx.send(f"Please provide the name a of a bound sheet you own. e.g. `/unbind Fun Trivia`")
            return

        if document := collection("bindings").find_one(
                {"locale": locale(ctx), "name_lower": sheet_name(name)}):

            if document["user"] == ctx.author.id:
                collection("bindings").delete_one({"locale": locale(ctx), "name_lower": sheet_name(name)})

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

    @cog_ext.cog_slash(name="sheets",
                        description="Lists all bound sheets in this context.")
    async def sheets(self, ctx: SlashContext):
        embeds = []

        async def add_embed():

            if ctx.guild:
                e = discord.Embed(description=f"Here are the bound sheets in {ctx.guild.name}.\nYou can start a quiz from the list by clicking on the corresponding button underneath this message.\nTo bind a sheet, use the `/bind` command.",
                                colour=discord.Color.blue())
            else:
                e = discord.Embed(description=f"Here are the sheets in this DM.\nYou can start a quiz from the list by clicking on the corresponding button underneath this message.\nTo bind a sheet, use the `/bind` command.",
                                colour=discord.Color.blue())

            embeds.append(e)
            embeds[-1].set_footer(text=f"To start a quiz using one of these sheets, use [/quiz <sheet name>], or click one of the buttons below!", icon_url=self.bot.user.avatar_url)

        await add_embed()
        for record in collection("bindings").find({"locale": locale(ctx)}):

            if len(embeds[-1].fields) < 4:
                embeds[-1].add_field(name=record["name"],
                                     value=f"Bound by <@{record['user']}>",
                                     inline=False)
            else:
                await add_embed()
                embeds[-1].add_field(name=record["name"],
                                     value=f"Bound by <@{record['user']}>",
                                     inline=False)

        for i in range(len(embeds)):
            embeds[i].title = f"Bound Sheets ({i+1}/{len(embeds)})"

        await send_menu_linker(ctx, embeds)

    @cog_ext.cog_slash(name="explore",
                        description="Lists premade sheets for you to use in your quizzes!")
    async def explore(self, ctx: commands.Context):
        embeds = []

        def add_embed():
            embeds.append(discord.Embed(description=f"Here are the Studybot official curated sheets, ready for you to use in the `/quiz` command! You can start a quiz from the list by clicking on the corresponding button underneath this message.\n[See the full list of sheets here](https://www.studybot.ca/explore.html)",
                            colour=discord.Color.blue()))
            embeds[-1].set_footer(text=f"To start a quiz using one of these sheets, use [/quiz <sheet name>], or click one of the buttons below!", icon_url=self.bot.user.avatar_url)

        add_embed()
        for record in await self.airtable.sheets:
            record = record["fields"]

            if len(embeds[-1].fields) < 4:
                embeds[-1].add_field(name=record["Sheet Name"],
                                     value=f"{record['Description']}\nBy: {record['Creator Discord Tag']}",
                                     inline=False)
            else:
                add_embed()
                embeds[-1].add_field(name=record["Sheet Name"],
                                     value=f"{record['Description']}\nBy: {record['Creator Discord Tag']}",
                                     inline=False)

        for i in range(len(embeds)):
            embeds[i].title = f"Explore ({i+1}/{len(embeds)})"

        await send_menu_linker(ctx, embeds)
