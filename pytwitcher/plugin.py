"""
Convenience class for plugins to subclass.
Provides settings interface.
"""

from copy import deepcopy


class BasePlugin:
    DEFAULTS = None

    def __init__(self, bot):
        self.bot = bot
        self._load_config()

    @classmethod
    def _get_config_key(cls):
        return cls.__name__

    @property
    def config(self):
        return self.bot.config[self._get_config_key()]

    @config.setter
    def config(self, value):
        self.bot.config[self._get_config_key()] = value

    def _load_config(self):
        defaults = deepcopy(self.DEFAULTS or {})

        try:
            loaded_config = self.config
        except KeyError:
            # No user config, use defaults
            self.config = defaults
        else:
            # Merge with defaults:, but don't overwrite
            defaults.update(loaded_config)
            self.config = defaults
