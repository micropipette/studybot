import discord
from discord.ext import commands
from discord_components import Button, ButtonStyle, InteractionType
import asyncio


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
