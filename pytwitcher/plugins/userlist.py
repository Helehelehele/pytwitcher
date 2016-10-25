from pytwitcher import event

class UserList:
    def __init__(self, bot):
        self.bot = bot

    @event.event(event.JOIN)
    def join(self):
        pass

    @event.event(event.PART)
    def part(self):
        pass

    @event.event(event.PRIVMSG)
    def privmsg(self):
        pass
