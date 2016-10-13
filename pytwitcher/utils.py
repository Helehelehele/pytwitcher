from collections import namedtuple


ALLOWED_KEYS = (
    'encoding',
    'flood_delay',
    'flood_rate_elevated',
    'flood_rate_normal',
    'nick',
    'password',
    'ssl',
)

Config = namedtuple('Config', ALLOWED_KEYS)


_UNESCAPES = (
    (r'\:', ';'),
    (r'\s', ' '),
    (r'\r', '\r'),
    (r'\n', '\n'),
    (r'\\', '\\'),
)

def _unescape(string):
    for s, r in _UNESCAPES:
        string = string.replace(s, r)
    return string

def decode(tagstring):
    """
    Decode a tag-string from an IRC message into a python dictionary.
    http://ircv3.net/specs/core/message-tags-3.2.html
    """

    if not tagstring:
        return {}

    tags = {}

    for tag in tagstring.split(';'):
        key, _, value = tag.partition('=')
        if value:
            value = _unescape(value)
        tags[key] = value

    return tags
