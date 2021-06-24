import discord
from discord.ext import commands
from config import version
from discord_components import Button, ButtonStyle

# Custom help command for Studybot

# TODO make more like the image https://media.discordapp.net/attachments/586550369685864470/829431840703250462/unknown.png
# MAKE IT A SINGLE LAYER

class StudyHelp(commands.HelpCommand):
    def __init__(self, **options):

        super().__init__(**options)

    async def send_bot_help(self, mapping: dict):
        embed = discord.Embed(colour=discord.Color.blue(),
                              description=f"The following are commands which you can run.\nType `{self.context.prefix}help [command]` for more info on a given command.")

        embed.set_footer(text=f"Studybot {version}")
        embed.set_author(name="Studybot Commands List", icon_url=self.context.bot.user.avatar_url, url="https://www.studybot.ca/")
        embed.set_thumbnail(url="https://cdn.discordapp.com/attachments/724671574459940974/856397833807462450/a_db09eb992c31a35306bb9157d78643bf.gif")

        components = [[Button(label="Invite Studybot to Your Server", style=ButtonStyle.URL,
                      url="https://discord.com/api/oauth2/authorize?client_id=804401459931643945&permissions=52288&scope=bot"),
                      Button(label="Vote for Us", style=ButtonStyle.URL,
                      url="https://top.gg/bot/804401459931643945/vote")],
                      [Button(label="Support Server", style=ButtonStyle.URL,
                      url="https://discord.gg/6qBxmpnnDW"),
                      Button(label="Tutorial Video", style=ButtonStyle.URL,
                      url="https://youtu.be/cdv8aSUOyMg")]]

        cog: commands.Cog
        for cog in mapping:

            if cog is not None and \
                    (cmds := await self.filter_commands(cog.get_commands())):
                # Check that cog exists and has commands for user to use

                for cmd in cmds:
                    embed.add_field(
                        name=self.context.prefix + cmd.qualified_name,
                        value=cmd.help if cmd.help else "No Description", inline=False)

        await self.context.send(embed=embed, components=components)

    async def send_command_help(self, command: commands.Command):
        filtered = await self.filter_commands([command])
        # check user actually is allowed to invoke the command
        if filtered:
            embed = discord.Embed(title=f"`{self.context.prefix}help {command.qualified_name} {command.signature}`",
                              colour=discord.Color.blue(),
                              description=command.help)

            embed.set_footer(icon_url=self.context.bot.user.avatar_url, text=f"Studybot {version}")

            if command.aliases:
                aliases = ", ".join(command.aliases)
                embed.add_field(
                    name="Aliases",
                    value=aliases,
                    inline=False,
                )

            await self.context.send(embed=embed)

    async def send_group_help(self, group: commands.Group):
        filtered = await self.filter_commands(
            group.commands
        )

        embed = discord.Embed(title=f"`{self.context.prefix}help {group.qualified_name} {group.signature}`",
                              colour=discord.Color.blue(),
                              description=group.help + "\n**Additional Commands in this group:**")

        embed.set_footer(icon_url=self.context.bot.user.avatar_url, text=f"Studybot {version}")

        command: commands.Command
        for command in filtered:
            embed.add_field(
                name=command.qualified_name,
                    value="`"+command.short_doc+"`")

        await self.context.send(embed=embed)

    async def send_cog_help(self, cog: commands.Cog):
        filtered = await self.filter_commands(
            cog.get_commands()
        )
        embed = discord.Embed(title=f"Commands in `{cog.qualified_name}`",
                              colour=discord.Color.blue())

        embed.set_footer(icon_url=self.context.bot.user.avatar_url, text=f"Studybot {version}")

        command: commands.Command
        for command in filtered:
            embed.add_field(
                name="`"+command.qualified_name+"`",
                    value=command.short_doc)

        await self.context.send(embed=embed)
