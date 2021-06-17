from discord.ext import tasks, commands
from utils.logger import logger

# This example uses tasks provided by discord.ext to create a task that posts guild count to Top.gg every 30 minutes.


class Topgg(commands.Cog):
    '''
    Set the configuration for the bot on the server
    '''
    def __init__(self, bot):
        self.bot: commands.Bot = bot
        self.update_stats.start()

    @tasks.loop(minutes=30)
    async def update_stats(self):
        """This function runs every 30 minutes to automatically update your server count."""
        try:
            await self.bot.topggpy.post_guild_count()
            logger.info(f'Posted server count ({self.bot.topggpy.guild_count})')
        except Exception as e:
            logger.info('Failed to post server count\n{}: {}'.format(type(e).__name__, e))

    @update_stats.before_loop
    async def startup_delay(self):
        await self.bot.wait_until_ready()
