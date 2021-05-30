import discord
from discord.ext import commands
from config import version

# Custom help command for Studybot


class StudyHelp(commands.HelpCommand):
    def __init__(self, **options):

        super().__init__(**options)

    async def send_bot_help(self, mapping: dict):
        embed = discord.Embed(title="Studybot Command Categories",
                              colour=discord.Color.blue(),
                              description=f"`{self.context.prefix}help [Category]` for more info on a given category.")

        embed.set_footer(icon_url=self.context.bot.user.avatar_url, text=f"Studybot {version}")

        cog: commands.Cog
        for cog in mapping:

            if cog is not None and \
                    await self.filter_commands(cog.get_commands()):
                # Check that cog exists and has commands for user to use
                embed.add_field(
                    name=(
                        cog.emoji if hasattr(
                            cog, "emoji") else "") + cog.qualified_name,
                    value=cog.description if cog.description else "No Description")

        await self.context.send(embed=embed)

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
