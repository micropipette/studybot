from dis_snek.models.scale import Scale
from dis_snek.models.application_commands import slash_command
from dis_snek.models.discord_objects.components import Button, ButtonStyles
from dis_snek.models.context import InteractionContext
from dis_snek.models.discord_objects.embed import Embed
from dis_snek.models.color import MaterialColors
from config import version


class General(Scale):
    @slash_command(name="invite",
        description="Provides the invite link to invite Studybot to your server!")
    async def invite(self, ctx: InteractionContext):
        components = [Button(label="Invite Studybot to your server!", style=ButtonStyles.URL,
                      url="https://discord.com/api/oauth2/authorize?client_id=804401459931643945&permissions=2147503104&scope=bot%20applications.commands")]
        await ctx.send(content="Click the link below to invite Studybot!", components=components)
        
    @slash_command(name="template", description="Gets the link for the template spreadsheet.")
    async def template(self, ctx: InteractionContext):
        e = Embed(title="Using the template")
        e.set_image(url="https://cdn.discordapp.com/attachments/804388848510435370/827998690886418463/ezgif-7-c601e2fb575f.gif")

        components = [
            Button(label="Template spreadsheet",
                   style=ButtonStyles.URL,
                   url="https://docs.google.com/spreadsheets/d/1Gbr6OeEWhZMCPOsvLo9Sx7XXcxgONfPR38FKzWdLjo0/copy"),
            Button(label="Tutorial Video",
                   style=ButtonStyles.URL,
                   url="https://youtu.be/cdv8aSUOyMg")]
        await ctx.send(
            embed=e,
            content="**Make a copy of this spreadsheet, and add your own questions!"
            "\nDon't forget to set the sheet to `anyone with link can view`**",
            components=components, ephemeral=True)
        
    @slash_command(name="help",
        description="Starting point for studybot commands")
    async def help(self, ctx: InteractionContext):
        embed = Embed(color=MaterialColors.BLUE,
                              description="The following are commands which you can run.")

        embed.set_footer(text=f"Studybot {version}")
        embed.set_author(name="Studybot Commands List", icon_url=ctx.bot.user.avatar.url, url="https://www.studybot.ca/")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/724671574459940974/856397833807462450/a_db09eb992c31a35306bb9157d78643bf.gif")

        components = [[Button(label="Invite Studybot to Your Server", style=ButtonStyles.URL,
                      url="https://discord.com/api/oauth2/authorize?client_id=804401459931643945&permissions=2147503104&scope=bot%20applications.commands"),
                      Button(label="Vote for Us", style=ButtonStyles.URL,
                      url="https://top.gg/bot/804401459931643945/vote")],
                      [Button(label="Support Server", style=ButtonStyles.URL,
                      url="https://discord.gg/6qBxmpnnDW"),
                      Button(label="Tutorial Video", style=ButtonStyles.URL,
                      url="https://youtu.be/cdv8aSUOyMg")]]

        quiz_scale = ctx.bot.get_scale("Quizzes")
        general_scale = ctx.bot.get_scale("General")

        for command in (quiz_scale.commands + general_scale.commands):
            embed.add_field(
                name="/" + command.name,
                value=command.description, inline=False)
        await ctx.send(embed=embed, components=components, ephemeral=True)


def setup(bot):
    General(bot)
