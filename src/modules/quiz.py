import gspread
import os
import random
from utils import locale
from db import collection, Airtable
from effectors.quiz_backend import listen_quiz, listen_quiz_mp

from dis_snek.models.scale import Scale
from dis_snek.models.application_commands import (slash_command,
                                                  OptionTypes, slash_option,
                                                  SlashCommandChoice)
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.color import MaterialColors
from effectors.button_menu import LinkerMenu
from logger import log


def sheet_name(sheet: str) -> str:
    '''
    Transforms a name into a cleaned name for storage
    (At the moment, just makes it lowercase)
    '''
    return sheet.lower()


class Quizzes(Scale):
    @slash_command(name="quiz",
                   description="Begins a quiz from a Studybot sheet.")
    @slash_option(name="gamemode", description="Singleplayer or multiplayer",
                  opt_type=OptionTypes.STRING, required=True,
                  choices=[
                      SlashCommandChoice(name="Singleplayer", value="singleplayer"),
                      SlashCommandChoice(name="Multiplayer", value="multiplayer")
                  ])
    @slash_option(name="sheet", description="Sheet URL or name of bound sheet",
                  opt_type=OptionTypes.STRING, required=True)
    async def quiz(self, ctx: InteractionContext, gamemode: str, sheet: str):
        '''
        Begins a singleplayer quiz from a Studybot sheet.
        Provide a sheet URL or the name of a Bound spreadsheet.
        Create your own sheet using the `template` command.
        '''
        await ctx.defer(ephemeral=(gamemode == "singleplayer"))
        
        if document := collection("bindings").find_one({"name_lower": sheet_name(sheet), "locale": locale(ctx)}):
            url = document["URL"]  # Search mongoDB
        elif record := await ctx.bot.airtable.find_sheet(sheet):
            
            url = record["fields"]["Link to Sheet"]  # Search airtable
        else:
            url = sheet  # Just URL

        try:
            sheet: gspread.Spreadsheet = ctx.bot.gc.open_by_url(url)
        except gspread.NoValidUrlKeyFound:
            await ctx.send(
                "Sheet not found."
                " Please check that your sheet exists and is shared with "
                "**anyone with link**.",
                ephemeral=(gamemode == "singleplayer"))
            return
        except gspread.exceptions.APIError:
            await ctx.send(
                "The sheet you linked is not shared publicly."
                " Please check that your sheet is shared with "
                "**anyone with link**.",
                ephemeral=(gamemode == "singleplayer"))
            return

        wks = sheet.get_worksheet(0)

        questions = wks.get_all_values()[1:]  # POP first row which is headers
        
        # Filter out questions with empty first column
        questions = [question for question in questions if question[0]]

        random.shuffle(questions)
        
        if gamemode == "singleplayer":
            await listen_quiz(ctx, sheet.title, questions)
            
        elif gamemode == "multiplayer":
            await listen_quiz_mp(ctx, sheet.title, questions)
    

    @slash_command(name="bind",
                   description="Binds a given spreadsheet to this context under a custom name.")
    @slash_option(name="url", description="Sheet URL",
                  opt_type=OptionTypes.STRING, required=True)
    @slash_option(name="name", description="Custom name for the sheet",
                  opt_type=OptionTypes.STRING, required=True)
    async def bind(self, ctx: InteractionContext, url: str, name: str):

        # NOTE: removed admin check because it cannot be implemented in slash commands

        if not collection("bindings").find_one(
                {"locale": locale(ctx), "name_lower": sheet_name(name)}):
            # Validate URL
            try:
                sheet: gspread.Spreadsheet = ctx.bot.gc.open_by_url(url)
            except gspread.NoValidUrlKeyFound:
                await ctx.send(
                    "Sheet not found."
                    " Please check that your sheet exists and is shared with "
                    "**anyone with link**.",
                    ephemeral=True)
                return
            except gspread.exceptions.APIError:
                await ctx.send(
                    "The sheet you linked is not shared publicly."
                    " Please check that your sheet is shared with "
                    "**anyone with link**.",
                    ephemeral=True)
                return

            collection("bindings").insert_one(
                {"locale": locale(ctx),
                 "name": name,
                 "name_lower": sheet_name(name),
                 "URL": url,
                 "user": ctx.author.id})

            if ctx.guild_id:
                await ctx.send(
                    f"Sheet successfully bound to this server with name `{name}`.")
            else:
                await ctx.send(
                    f"Sheet successfully bound to DM with name `{name}`.")

        elif ctx.guild_id:
            await ctx.send(
                f"A sheet with name `{name}` already exists in "
                "this server (names are case insensitive)! Try another one.", ephemeral=True)
        else:
            await ctx.send(
                f"A sheet with name `{name}` already exists in "
                "this DM (names are case insensitive)! Try another one.", ephemeral=True)


    @slash_command(name="unbind",
                   description="Unbinds the sheet with the specified name, if you own it.")
    @slash_option(name="name", description="Custom name of the sheet",
                  opt_type=OptionTypes.STRING, required=True)
    async def unbind(self, ctx: InteractionContext, name: str = None):

        if document := collection("bindings").find_one(
                {"locale": locale(ctx), "name_lower": sheet_name(name)}):

            if document["user"] == ctx.author.id:
                collection("bindings").delete_one({"locale": locale(ctx), "name_lower": sheet_name(name)})

                if ctx.guild_id:
                    await ctx.send(
                        f"Sheet with name `{name}` successfully unbound from this server.")
                else:
                    await ctx.send(
                        f"Sheet with name `{name}` successfully unbound from this DM.")
            else:
                await ctx.send(f"You are not the owner of sheet `{name}`!", ephemeral=True)

        else:
            await ctx.send(
                f"A sheet with name `{name}` was not found. "
                "Make sure you are referring to a sheet you previously bound using `/bind`.",
                ephemeral=True)

    @slash_command(name="sheets",
                   description="Lists all bound sheets in this context.")
    async def sheets(self, ctx: InteractionContext):
        embeds = []

        async def add_embed():

            if ctx.guild_id:
                e = Embed(description=f"Here are the bound sheets in this server."
                          "\nYou can start a quiz from the list by clicking on the"
                          "corresponding button underneath this message.\nTo bind a sheet, use the `/bind` command.",
                                color=MaterialColors.BLUE)
            else:
                e = Embed(description=f"Here are the sheets in this DM.\n"
                          "You can start a quiz from the list by clicking on the corresponding "
                          "button underneath this message.\nTo bind a sheet, use the `/bind` command.",
                                color=MaterialColors.BLUE)

            embeds.append(e)
            embeds[-1].set_footer(text=f"To start a quiz using one of these sheets, use [/quiz <sheet name>], or click one of the buttons below!", icon_url=self.bot.user.avatar.url)

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

        paginator = LinkerMenu.create_from_embeds(ctx.bot, *embeds, timeout=120)
        await paginator.send(ctx)

    @slash_command(name="explore",
                   description="Lists premade sheets for you to use in your quizzes!")
    async def explore(self, ctx: InteractionContext):
        embeds = []

        def add_embed():
            embeds.append(Embed(description=f"Here are the Studybot official curated sheets, ready for you to use in the `/quiz` command! You can start a quiz from the list by clicking on the corresponding button underneath this message.\n[See the full list of sheets here](https://www.studybot.ca/explore.html)",
                            color=MaterialColors.BLUE))
            embeds[-1].set_footer(text=f"To start a quiz using one of these sheets, click one of the buttons below!", icon_url=self.bot.user.avatar.url)

        add_embed()
        for record in await ctx.bot.airtable.sheets:
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

        paginator = LinkerMenu.create_from_embeds(ctx.bot, *embeds, timeout=120)
        await paginator.send(ctx)

def setup(bot):
    bot.airtable = Airtable()
    with open("temp.json", "w") as f:
        f.write(os.environ.get("SHEETS"))
    bot.gc = gspread.service_account(filename="temp.json")
    os.remove("temp.json")
    Quizzes(bot)
    log.info("Quiz Module Loaded")
