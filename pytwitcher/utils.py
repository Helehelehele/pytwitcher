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
