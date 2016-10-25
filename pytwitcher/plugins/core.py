from pytwitcher import event


class Core:
    def __init__(self, bot):
        self.bot = bot

    async def on_login_failed(self):
        # just log, irc will disconnect us automatically
        pass
