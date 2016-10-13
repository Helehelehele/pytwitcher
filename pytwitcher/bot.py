from . import base
from . import utils


class IrcBot(base.IrcObject):
    @property
    def nick(self):
        return self.config.nick

    @utils.future
    def privmsg(self, target, message):
        # WHISPER event is receive-only
        # You *have* to go through any valid user/room to make sure message goes through
        if isinstance(target, User):
            return self.send_line('PRIVMSG {target} :.w {target} {message}'.format(
                target=target, message=message,
            ))
        elif isinstance(target, Channel):
            return self.send_line('PRIVMSG {target} :{message}'.format(
                target=target, message=message,
            ))

    # alias
    whisper = privmsg

    def action(self, target, message):
        """
        Sidenote: ACTION in whispers does not get rendered correctly
        """
        return self.privmsg(target, '.me {}'.format(message))

    @utils.future
    def join(self, channel):
        return self.send_line('JOIN {}'.format(channel))

    @utils.future
    def part(self, channel):
        return self.send_line('PART {}'.format(channel))

    @utils.future
    def quit(self):
        return self.send_line('QUIT')
