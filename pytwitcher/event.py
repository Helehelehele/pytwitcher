"""
Define all server events that the server can send us.
Everything else will get dropped.
"""

class Raw:
    __slots__ = ('name', 're')

    name = None
    re = None

    def __init__(self, name, regexp):
        self.name = name
        self.re = regexp


# Numeric Replies

RPL_NAMREPLY = Raw('RPL_NAMREPLY', r':(?P<srv>\S+) 353 (?P<me>\S+) (?P<m>\S+) (?P<channel>\S+) :(?P<data>.*)')
RPL_ENDOFNAMES = Raw('RPL_ENDOFNAMES', r':(?P<srv>\S+) 366 (?P<me>\S+) (?P<channel>\S+) :(?P<data>.*)')

RPL_MOTDSTART = Raw('RPL_MOTDSTART', r':(?P<srv>\S+) 375 (?P<me>\S+) :(?P<data>.*)')
RPL_MOTD = Raw('RPL_MOTD', r':(?P<srv>\S+) 372 (?P<me>\S+) :(?P<data>.*)')
RPL_ENDOFMOTD = Raw('RPL_ENDOFMOTD', r':(?P<srv>\S+) 376 (?P<me>\S+) :(?P<data>.*)')

ERR_UNKNOWNCOMMAND = Raw('ERR_UNKNOWNCOMMAND', r':(?P<srv>\S+) 421 (?P<me>\S+) :(?P<data>.*)')


# Message Replies

CAP_ACK = Raw('CAP_ACK', ':(?P<srv>\S+) CAP * ACK :(?P<data>.*)')

PING = Raw('PING', r'PING :?(?P<data>.*)')
PONG = Raw('PONG', r':(?P<server>\S+) PONG (?P=server)(?: :)?(?P<data>.*)')

JOIN = Raw('JOIN', r':(?P<mask>\S+) JOIN (?P<channel>\S+)')
PART = Raw('PART', r':(?P<mask>\S+) PART (?P<channel>\S+)')

MODE = Raw('MODE', r':(?P<mask>jtv) (?P<event>MODE) (?P<target>\S+) (?P<modes>\S+)( (?P<data>\S+))?')

PRIVMSG = Raw('PRIVMSG', r'(?:@(?P<tags>\S+) )?:(?P<mask>[^!]+)(?:\S+ )(?P<event>PRIVMSG) (?P<channel>\S+) :(?P<data>.+)')
WHISPER = Raw('WHISPER', r'(?:@(?P<tags>\S+) )?:(?P<mask>[^!]+)(?:\S+ )(?P<event>WHISPER) (?P<me>\S+) :(?P<data>.+)')
NOTICE = Raw('NOTICE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>NOTICE) (?P<target>\S+) :(?P<data>.+)')
USERNOTICE = Raw('USERNOTICE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>USERNOTICE) (?P<target>\S+) :(?P<data>.+)')

HOSTTARGET = Raw('HOSTTARGET', r':(?P<mask>tmi.twitch.tv) HOSTTARGET (?P<hosting_channel>\S+) :(?P<target_channel>\S+) (?P<number>\d+)')

CLEARCHAT = Raw('CLEARCHAT', r':(?P<mask>tmi.twitch.tv) CLEARCHAT (?P<target>\S+)( :(?P<data>\S+))?')

USERSTATE = Raw('USERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>USERSTATE) (?P<target>\S+)')
GLOBALUSERSTATE = Raw('GLOBALUSERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>GLOBALUSERSTATE)')
ROOMSTATE = Raw('USERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>ROOMSTATE) (?P<target>\S+)')

RECONNECT = Raw('RECONNECT', r'RECONNECT')

