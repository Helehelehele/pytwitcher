"""
Registry is the object handling all external events definition.
"""
import asyncio
from collections import defaultdict, deque
import inspect
import logging
from typing import Tuple

from . import utils
from . import event


logger = logging.getLogger(__name__)


class Registry:
    def __init__(self, config: dict):
        self.config = config

        # key = on_event_name value = list of callbacks to call with the data
        # things that come from irc
        self.irc_events_re = deque()
        self.irc_events = defaultdict(deque)

        # on_ for the bot itself (use bot.notify to trigger)
        self.listeners = defaultdict(list)

        self.plugins = {}

    def get_event_matches(self, data):
        events = self.irc_events
        for key, matcher in self.irc_events_re:
            match = matcher(data)
            if match is not None:
                yield match, events[key]

    def reload_plugin(self, name: str):
        logging.debug('Reloading plugin %s', name)
        plugin = self.remove_plugin(name)
        if plugin is None:
            raise ValueError('Plugin is not loaded')

        self.add_plugin(plugin)

    def add_plugin(self, plugin):
        self.plugins[type(plugin).__name__] = plugin

        for name, member in inspect.getmembers(plugin):
            # Register IRC events
            if isinstance(member, event.event):
                self.add_irc_event(member)
            # Register listeners
            elif name.startswith('on_') or name.startswith('handle_'):
                self.add_listener(member)

    def remove_plugin(self, name: str):
        plugin = self.plugins.pop(name, None)
        if plugin is None:
            return plugin

        for name, member in inspect.getmembers(plugin):
            # Remove IRC events
            if isinstance(member, event.event):
                self.remove_irc_event(member)
            # Remove listeners
            elif name.startswith(('on_', 'handle_')):
                self.remove_listener(member)

        try:
            unloader = getattr(plugin, 'unload')
        except AttributeError:
            pass
        else:
            unloader()

        return plugin

    def add_listener(self, func, name: str = None):
        name = name or func.__name__
        logger.debug('Adding %s to %s listener', func, name)

        if name.startswith('on_') and not asyncio.iscoroutinefunction(func):
            raise ValueError('`on_` listeners must be coroutines')
        elif name.startswith('handle_') and asyncio.iscoroutinefunction(func):
            raise ValueError('`handle_` listeners must not be coroutines')
        else:
            raise ValueError('Listeners must start with `on_` or `handle_`')

        self.listeners[name].append(func)

    def remove_listener(self, func, name: str = None):
        name = name or func.__name__
        logger.debug('Removing %s from %s listener', func, name)

        if name in self.listeners:
            try:
                self.listeners[name].remove(func)
            except ValueError:
                pass

    def add_irc_event(self, irc_event: event.event, insert: bool = False):
        if not asyncio.iscoroutinefunction(irc_event.callback):
            raise ValueError('Event handlers must be coroutines')

        # key is used to link irc_events_re and irc_events
        matcher = irc_event.compile(self.config)
        key = irc_event.key  # = regexp

        if key not in self.irc_events:
            if insert:
                self.irc_events_re.appendleft((key, matcher))
            else:
                self.irc_events_re.append((key, matcher))

        if insert:
            self.irc_events[key].appendleft(irc_event)
        else:
            self.irc_events[key].append(irc_event)


    def remove_irc_event(self, irc_event: event.event):
        all_events = self.irc_events
        key = irc_event.key
        delete = []

        if key in all_events:
            # someone else registered this regex but not this event
            try:
                all_events[key].remove(irc_event)
            except ValueError:
                pass

            if not all_events[key]:
                # No more events listening to this, remove it from the matchers
                delete.append(key)
                del all_events[key]

        self.irc_events_re = [r for r in self.irc_events_re if r[0] not in delete]

    def recompile(self, config: dict):
        logging.info('Recompiling registry using config %s', config)
        self.config = config

        events_re = self.irc_events_re
        events = self.irc_events

        new_events_re = deque()
        for key, _ in events_re:
            # All events compile to the same matcher, just take the first one
            new_events_re.append((key, events[key][0].compile(config)))

        self.irc_events_re = new_events_re
