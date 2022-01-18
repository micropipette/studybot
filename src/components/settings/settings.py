from discord.ext import commands
from discord_slash.utils import manage_commands
from utils.utilities import locale
from db import collection

from discord_components import Button, ButtonStyle, ActionRow

# Slash command stuff
from discord_slash import SlashContext
from discord_slash import cog_ext


def default_settings(ctx):
    '''
    Returns default settings document for servers
    '''
    return {"_id": locale(ctx), "prefix": "-", "admin-bind": True}


class Settings(commands.Cog):
    '''
    Set the configuration for the bot on the server
    '''
    def __init__(self, bot):
        self.bot: commands.AutoShardedBot = bot

    @cog_ext.cog_slash(
        name="invite",
        description="Provides the invite link to invite Studybot to your server!"
    )
    async def invite(self, ctx: SlashContext):
        components = [ActionRow(Button(label="Invite Studybot to your server!", style=ButtonStyle.URL,
                      url="https://discord.com/api/oauth2/authorize?client_id=804401459931643945&permissions=314368&scope=bot")).to_dict()]
        await ctx.send(content="Click the link below to invite Studybot!", components=components)

    @cog_ext.cog_slash(
        name="allowuserbind",
        description="Control whether users are allowed to bind sheets",
        options=manage_commands.create_option(name="allow", description="Allow users to bind sheets", option_type=5, required=True)
    )
    @commands.has_guild_permissions(administrator=True)
    async def allowuserbind(self, ctx: SlashContext, allow: bool):
        '''
        allows users to bind or not bind sheets to the server
        '''
        if settings := collection("settings").find_one(locale(ctx)):
            collection("settings").update_one(
                {"_id": locale(ctx)}, {"$set": {"admin-bind": not allow}})
        else:
            # Need a new setings doc
            settings = default_settings(ctx)
            settings["admin-bind"] = not allow
            collection("settings").insert_one(settings)

        if allow:
            await ctx.send("All users are now allowed to bind sheets.")
        else:
            await ctx.send("Only **Administrators** are now allowed to bind sheets.")
