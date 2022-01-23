from dis_snek.models.scale import Scale
from dis_snek.models.listener import listen


DEPR_MESSAGE = "Discord is removing support for bots using message commands." \
    " Studybot has switched to using slash commands. Please type `/help` to see the new commands," \
    " or re-invite the bot if you cannot see the slash commands using this link: " \
    "https://discord.com/api/oauth2/authorize?client_id=804401459931643945&permissions=2147503104&scope=bot%20applications.commands"


class Deprecation(Scale):
    @listen()
    async def on_message_create(self, event):
        if "-quiz" in event.message.content or \
        "-help" in event.message.content or \
            self.bot.user.mention in event.message.content:
                
            if channel := event.message.channel:
                await channel.send(DEPR_MESSAGE)
            else:
                await event.message.author.send(DEPR_MESSAGE)
                

def setup(bot):
    Deprecation(bot)
