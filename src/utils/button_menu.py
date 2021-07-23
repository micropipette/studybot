import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, InteractionType
import asyncio
import datetime


async def send_menu(ctx: commands.context, embeds: discord.Embed):
    '''
    Send embeds with buttons for navigation
    '''
    current_page = 0  # Index
    last_page = len(embeds) - 1  # Last allowable index

    if len(embeds) == 1:
        await ctx.send(embed=embeds[0])
        return

    def components(current_page):
        return[[Button(label="Previous", style=ButtonStyle.blue, emoji="◀", disabled=(current_page == 0)),
                Button(label="Next", style=ButtonStyle.blue, emoji="▶", disabled=(current_page == last_page))]]

    msg = await ctx.send(embed=embeds[0], components=components(current_page))

    while 1:

        def check(res):
            return res.author.id == ctx.author.id and res.message.id == msg.id

        try:
            res = await ctx.bot.wait_for("button_click", timeout=120, check=check)

            if res.component.label == "Previous":
                current_page -= 1
            elif res.component.label == "Next":
                current_page += 1

            await res.respond(type=InteractionType.UpdateMessage,
                              components=components(current_page),
                              embed=embeds[current_page])

        except asyncio.TimeoutError:
            await msg.edit(
                components=[])
            return


async def send_menu_linker(ctx: commands.context, embeds: discord.Embed):
    '''
    Send embeds with buttons for navigation, with links for quiz
    '''
    current_page = 0  # Index
    last_page = len(embeds) - 1  # Last allowable index

    def components(current_page):
        return [[Button(label="Previous", style=ButtonStyle.blue, emoji="◀", disabled=(current_page == 0)),
                Button(label="Next", style=ButtonStyle.blue, emoji="▶", disabled=(current_page == last_page))],
                [Button(label=field.name) for field in embeds[current_page].fields]] 

    if embeds[current_page].fields:
        msg = await ctx.send(embed=embeds[0], components=components(current_page))
    else:
        msg = await ctx.send(embed=embeds[0])
        return

    # async def explore_click_listener(res):
    #     if res.author.id == ctx.author.id and res.message.id == msg.id:
    #         pass

    # ctx.bot.add_listener(explore_click_listener, "on_button_click")
    # This is a cool idea

    while 1:

        def check(res):
            return res.author.id == ctx.author.id and res.message.id == msg.id

        try:
            res = await ctx.bot.wait_for("button_click", timeout=120, check=check)

            quiz = False

            if res.component.label == "Previous":
                current_page -= 1
            elif res.component.label == "Next":
                current_page += 1
            else:
                quiz = True

            await res.respond(type=InteractionType.UpdateMessage,
                            components=components(current_page),
                            embed=embeds[current_page])

            if quiz:
                quiz_cog = ctx.bot.get_cog("Quizzes")
                asyncio.create_task(quiz_cog.quiz(ctx, sheet=res.component.label))
                # NOTE: Allows the explore menu to spawn quizzes concurrently!

        except asyncio.TimeoutError:
            await msg.edit(
                components=[])
            return
