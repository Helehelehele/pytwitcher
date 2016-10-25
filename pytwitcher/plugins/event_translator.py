from pytwitcher import event


class EventTranslator:
    """
    Defines translation from raw events to the dispatcher
    """

    def __init__(self, bot):
        self.bot = bot
        # One time events that we only need to register temporarily
        self.before_connect_events = [
            event.event(event.NOTICE, callback=self.check_login),
            event.event(event.RPL_ENDOFMOTD, callback=self.remove_events),
            event.event(event.GLOBALUSERSTATE, callback=self.set_user_state)
        ]

    def handle_connection_attempted(self):
        for irc_event in self.before_connect_events:
            self.bot.add_irc_event(irc_event)

    async def check_login(self, tags, mask, event, target, data):
        if data == 'Login authentication failed':
            self.bot.notify('login_failed')

    async def remove_events(self, **kwargs):
        for irc_event in self.before_connect_events:
            self.bot.remove_irc_event(irc_event)

    async def set_user_state(self, data):
        pass

    @event.event(event.NOTICE)
    async def notice(self, tags, target, data):
        if tags and 'msg-id' in tags:
            self.bot.notify('notice', notice_type=enum[tags['msg-id']])

    @event.event(event.USERNOTICE)
    async def usernotice(self, tags, target, data):
        pass

    @event.event(event.PRIVMSG)
    async def privmsg(self, tags, target, data):
        # handle resubscribe from twitchnotify
        pass

    @event.event(event.RECONNECT)
    async def reconnect(self):
        # Log
        self.bot.create_connection()
