"""
Define all server events that the server can send us.
Everything else will get dropped.
"""

class raw(str):
    name = None
    re = None

    @classmethod
    def new(cls, name, regexp):
        r = cls(name)
        r.name = name
        r.re = regexp

        return r

# Numeric Replies

RPL_NAMREPLY = raw.new('RPL_NAMREPLY', r':(?P<srv>\S+) 353 (?P<me>\S+) (?P<m>\S+) (?P<channel>\S+) :(?P<data>.*)')
RPL_ENDOFNAMES = raw.new('RPL_ENDOFNAMES', r':(?P<srv>\S+) 366 (?P<me>\S+) (?P<channel>\S+) :(?P<data>.*)')

RPL_MOTDSTART = raw.new('RPL_MOTDSTART', r':(?P<srv>\S+) 375 (?P<me>\S+) :(?P<data>.*)')
RPL_MOTD = raw.new('RPL_MOTD', r':(?P<srv>\S+) 372 (?P<me>\S+) :(?P<data>.*)')
RPL_ENDOFMOTD = raw.new('RPL_ENDOFMOTD', r':(?P<srv>\S+) 376 (?P<me>\S+) :(?P<data>.*)')

ERR_UNKNOWNCOMMAND = raw.new('ERR_UNKNOWNCOMMAND', r':(?P<srv>\S+) 421 (?P<me>\S+) :(?P<data>.*)')


# Message Replies

CAP_ACK = raw.new('CAP_ACK', ':(?P<srv>\S+) CAP * ACK :(?P<data>.*)')

PING = raw.new('PING', r'PING :?(?P<data>.*)')
PONG = raw.new('PONG', r':(?P<server>\S+) PONG (?P=server)(?: :)?(?P<data>.*)')

JOIN = raw.new('JOIN', r':(?P<mask>\S+) JOIN (?P<channel>\S+)')
PART = raw.new('PART', r':(?P<mask>\S+) PART (?P<channel>\S+)')

MODE = raw.new('MODE', r':(?P<mask>jtv) (?P<event>MODE) (?P<target>\S+) (?P<modes>\S+)( (?P<data>\S+))?')

PRIVMSG = raw.new('PRIVMSG', r'(?:@(?P<tags>\S+) )?:(?P<mask>[^!]+)(?:\S+ )(?P<event>PRIVMSG) (?P<target>\S+) :(?P<data>.+)')
WHISPER = raw.new('WHISPER', r'(?:@(?P<tags>\S+) )?:(?P<mask>[^!]+)(?:\S+ )(?P<event>WHISPER) (?P<me>\S+) :(?P<data>.+)')
NOTICE = raw.new('NOTICE', r'(?:@(?P<tags>\S+) )?:(?P<mask>[^!]+)(?:\S+ )(?P<event>NOTICE) (?P<target>\S+) :(?P<data>.+)')
USERNOTICE = raw.new('USERNOTICE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>USERNOTICE) (?P<target>\S+) :(?P<data>.+)')

HOSTTARGET = raw.new('HOSTTARGET', r':(?P<mask>tmi.twitch.tv) HOSTTARGET (?P<hosting_channel>\S+) :(?P<target_channel>\S+) (?P<number>\d+)')

CLEARCHAT = raw.new('CLEARCHAT', r':(?P<mask>tmi.twitch.tv) CLEARCHAT (?P<target>\S+)( :(?P<data>\S+))?')

USERSTATE = raw.new('USERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>USERSTATE) (?P<target>\S+)')
GLOBALUSERSTATE = raw.new('GLOBALUSERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>GLOBALUSERSTATE)')
ROOMSTATE = raw.new('USERSTATE', r'(?:@(?P<tags>\S+) )?:(?P<mask>tmi.twitch.tv) (?P<event>ROOMSTATE) (?P<target>\S+)')

RECONNECT = raw.new('RECONNECT', r'RECONNECT')

