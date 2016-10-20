import asyncio
from collections import defaultdict
import importlib
import random
import signal
import ssl
import sys
import traceback

import certifi

from . import protocol
from . import registry
from . import utils


class IrcObject:

    HOST = 'irc.chat.twitch.tv'
    CAPABILITIES = ('membership', 'commands', 'tags')

    DEFAULTS = {
        'encoding': 'utf8',
        'flood_delay': 30,
        'flood_rate_elevated': 100,
        'flood_rate_normal': 20,
        'nick': None,
        'password': None,
        'ssl': True,
    }

    def __init__(self, loop: asyncio.BaseEventLoop = None, **config):
        if loop is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        self.loop = loop
        self.config = utils.Config(**dict(self.DEFAULTS, **config))

        self.encoding = self.config.encoding
        self.registry = registry.Registry(self.config)
        self.queue = asyncio.Queue(loop=self.loop)

        asyncio.ensure_future(self.process_queue(), loop=self.loop)

    def load_plugin(self, name: str):
        if name in self.registry.plugins:
            return

        lib = importlib.import_module(name)
        if not hasattr(lib, 'setup'):
            del lib
            del sys.modules[name]
            raise ValueError('plugin does not have a setup function')

        lib.setup(self)

    def unload_plugin(self, name: str):
        # TODO
        pass

    # registry shortcuts

    def add_plugin(self, plugin):
        self.registry.add_plugin(plugin)

    def add_listener(self, func, name=None):
        self.registry.add_listener(func, name=name)

    def remove_listener(self, func, name=None):
        self.registry.remove_listener(func, name=name)

    def recompile(self):
        self.registry.recompile(self.config)

    def add_irc_event(self, event, insert=False):
        self.registry.add_irc_event(event, insert=insert)

    def remove_irc_event(self, event):
        self.registry.remove_irc_event(event)

    async def on_error(self, event_method, exc, *args, **kwargs):
        traceback.print_exc()

    async def _run_listener(self, coro, listener_name, *args, **kwargs):
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception as exc:
            try:
                await self.on_error(listener_name, exc, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def notify(self, listener_name, *args, **kwargs):
        async_listener = 'on_' + listener_name
        sync_listener = 'handle_' + listener_name

        if sync_listener in self.registry.listeners:
            for func in self.registry.listeners[sync_listener]:
                # FIXME: doesn't handle errors
                func(*args, **kwargs)

        if async_listener in self.registry.listeners:
            for coro in self.registry.listeners[async_listener]:
                asyncio.ensure_future(self._run_listener(coro, listener_name, *args, **kwargs), loop=self.loop)

    def process_data(self, data):
        for match, events in self.registry.get_event_matches(data):
            match = match.groupdict()
            for event in events:
                asyncio.ensure_future(event.callback(**match), loop=self.loop)

    def get_connection_data(self):
        if self.config.ssl:
            return {
                'host': self.HOST,
                'port': 443,
                'ssl': ssl.create_default_context(cafile=certifi.where()),
            }
        else:
            return {
                'host': self.HOST,
                'port': 6667,
            }

    def create_connection(self):
        task = asyncio.ensure_future(
            self.loop.create_connection(lambda: protocol.IrcProtocol(self), **self.get_connection_data()),
            loop=self.loop,
        )
        task.add_done_callback(self.connection_made)

    def connection_made(self, future: asyncio.Future):
        # Close the old one (in case of reconnections)
        if hasattr(self, 'protocol'):
            self.protocol.close()  # pylint: disable=access-member-before-definition

        try:
            _, proto = future.result()
        except Exception as e:
            # TODO: log
            self.loop.call_later(3, self.create_connection)
        else:
            self.protocol = proto  # pylint: disable=attribute-defined-outside-init
            self.start_handshake()
            self.notify('connection_attempted')

    def start_handshake(self):
        self.send('CAP REQ :{}'.format(' '.join('twitch.tv/{}'.format(cap) for cap in self.CAPABILITIES)))
        if not self.config.nick:
            # Anonymous login
            self.send('NICK justinfan{}'.format(random.randrange(999999)))
        else:
            self.send('PASS {}'.format(self.config.password))
            self.send('NICK {}'.format(self.config.nick))

    def send_line(self, data):
        f = asyncio.Future(loop=self.loop)
        self.queue.put_nowait((f, data))
        return f

    async def process_queue(self):
        flood_rate = self.config.flood_delay / self.config.flood_rate_normal
        while True:
            future, data = await self.queue.get()
            future.set_result(True)
            self.send(data)
            # TODO: flood_rate calculation according to user state
            await asyncio.sleep(flood_rate, loop=self.loop)

    def send(self, data):
        try:
            self.protocol.write(data)
        except AttributeError:
            # Not connected yet
            # FIXME: during reconnection, everything is lost, probably have to
            # repush into the queue at the right place
            pass

    def add_signal_handlers(self):
        try:
            self.loop.add_signal_handler(signal.SIGHUP, self.SIGHUP)
        except (RuntimeError, AttributeError):
            # windows
            pass

        try:
            self.loop.add_signal_handler(signal.SIGINT, self.SIGINT)
        except (RuntimeError, NotImplementedError):
            # anaconda
            pass

    def SIGHUP(self):
        # TODO
        self.reload()

    def SIGINT(self):
        # TODO
        self.notify('SIGINT')
        # Cleanup
        self.loop.stop()

    def run(self, forever: bool = True):
        self.create_connection()
        self.add_signal_handlers()

        if forever:
            self.loop.run_forever()
