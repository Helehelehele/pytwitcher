import asyncio
import importlib
import logging
import random
import signal
import ssl
import sys
import traceback

import certifi

from . import protocol
from . import registry
from . import utils


logger = logging.getLogger(__name__)


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

        # TOOD: say in the docs that we take ownership of the loop, we close it
        # ourselves in run()
        self.loop = loop
        self.config = dict(self.DEFAULTS, **config)

        self.encoding = self.config['encoding']
        self.registry = registry.Registry(self.config)
        self.queue = asyncio.Queue(loop=self.loop)

        asyncio.ensure_future(self._process_queue(), loop=self.loop)

    def load_plugin(self, name: str):
        # NOTE: name is full path to the plugin, eg path.Plugin, not path
        logger.debug('Trying to load %s', name)
        if name in self.registry.plugins:
            return

        module_name, class_name = name.rsplit('.', 1)

        try:
            module = importlib.import_module(module_name)
        except ImportError:
            raise ValueError('%s is not importable', module_name)

        try:
            klass = getattr(module, class_name)
        except AttributeError:
            del module
            del sys.modules[module_name]
            raise ValueError('%s has no attribute %s', module_name, class_name)

        self.registry.add_plugin(klass(self))
        logger.info('Loaded `%s`', name)

    def unload_plugin(self, name: str):
        plugin = self.registry.remove_plugin(name)
        del plugin
        logger.info('Unloaded `%s`', name)

    # registry shortcuts

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
        logger.exception('Error when calling %s', event_method)
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
        logger.debug('Received notify request %s with args %s, %s', listener_name, args, kwargs)
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
        logger.debug('Processing data from IRC: %s', data)
        for match, events in self.registry.get_event_matches(data):
            match = match.groupdict()
            for event in events:
                asyncio.ensure_future(event.callback(**match), loop=self.loop)

    def _get_connection_data(self):
        if self.config['ssl']:
            logger.debug('Connecting using SSL')
            return {
                'host': self.HOST,
                'port': 443,
                'ssl': ssl.create_default_context(cafile=certifi.where()),
            }
        else:
            logger.debug('Connecting without SSL')
            return {
                'host': self.HOST,
                'port': 6667,
            }

    def create_connection(self):
        logger.debug('Scheduling new connection')
        task = asyncio.ensure_future(
            self.loop.create_connection(lambda: protocol.IrcProtocol(self), **self._get_connection_data()),
            loop=self.loop,
        )
        task.add_done_callback(self._connection_made)

    def _connection_made(self, future: asyncio.Future):
        logger.info('Received connection to Twitch')
        # Close the old one (in case of reconnections)
        if hasattr(self, 'protocol'):
            logger.debug('Closing old protocol')
            self.protocol.close()  # pylint: disable=access-member-before-definition

        try:
            _, proto = future.result()
        except:
            logger.warning('Could not fetch protocol, rescheduling connection', exc_info=True)
            self.loop.call_later(3, self.create_connection)
        else:
            self.protocol = proto  # pylint: disable=attribute-defined-outside-init
            self._start_handshake()
            self.notify('connection_attempted')

    def _start_handshake(self):
        self.send('CAP REQ :{}'.format(' '.join('twitch.tv/{}'.format(cap) for cap in self.CAPABILITIES)))
        if not self.config['nick']:
            logger.debug('Anonymous login requested')
            # Anonymous login
            self.send('NICK justinfan{}'.format(random.randrange(999999)))
        else:
            logger.debug('OAuth login requested')
            self.send('PASS {}'.format(self.config['password']))
            self.send('NICK {}'.format(self.config['nick']))

    def send_line(self, data):
        fut = self.loop.create_future()
        self.queue.put_nowait((fut, data))
        return fut

    async def _process_queue(self):
        flood_rate = self.config['flood_delay'] / self.config['flood_rate_normal']
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
            logger.warning('Cannot send data without active connection')
            # FIXME: during reconnection, everything is lost, probably have to
            # repush into the queue at the right place

    def _add_signal_handlers(self):
        try:
            self.loop.add_signal_handler(signal.SIGHUP, self.SIGHUP)
        except (RuntimeError, AttributeError):
            # windows
            logger.debug('Could not add SIGHUP signal handler, ignoring')

        try:
            self.loop.add_signal_handler(signal.SIGINT, self.SIGINT)
        except (RuntimeError, NotImplementedError):
            # anaconda
            logger.debug('Could not add SIGINT signal handler, ignoring')

    def SIGHUP(self):
        logger.info('Received SIGHUP signal')
        # TODO
        self.reload()

    def SIGINT(self):
        logger.info('Received SIGINT signal')
        # TODO: Cleanup our things: close transport
        self.notify('stop')
        self.loop.stop()

    def run(self, forever: bool = True):
        self.create_connection()
        self._add_signal_handlers()

        if forever:
            self.loop.run_forever()
            self._cleanup()

    def _cleanup(self):
        # Cancel remaining tasks and close the loop
        gathered = asyncio.gather(*asyncio.Task.all_tasks(loop=self.loop))
        gathered.cancel()
        try:
            self.loop.run_until_complete(gathered)
        except asyncio.CancelledError:
            pass

        self.loop.close()
