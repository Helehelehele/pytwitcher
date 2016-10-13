import asyncio
import random
import signal
import ssl

from . import protocol
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

    def __init__(self, loop=None, **config):
        if loop is None:
            try:
                loop = asyncio.get_event_loop()
            except RuntimeError:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

        self.loop = loop
        self.config = utils.Config(**dict(self.DEFAULTS, **config))

        self.encoding = self.config.encoding
        self.queue = asyncio.Queue(loop=self.loop)

        asyncio.ensure_future(self.process_queue(), loop=self.loop)

    def notify(self, event_name, *args, **kwargs):
        # TODO
        pass

    def dispatch(self, data):
        # TODO
        pass

    def get_connection_data(self):
        if self.config.ssl:
            # TODO: ship the twitch ssl crt and use it with an option in case
            # a weird system where there are no default certs (or use certifi)
            # can specify cadata or cafile
            return {
                'host': self.HOST,
                'port': 443,
                'ssl': ssl.create_default_context(),
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

    def connection_made(self, future):
        # Close the old one (in case of reconnections)
        if hasattr(self, 'protocol'):
            self.protocol.close()

        try:
            _, protocol = future.result()
        except Exception as e:
            self.loop.call_later(3, self.create_connection)
        else:
            self.protocol = protocol
            self.start_handshake()
            self.notify('connection_made')

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
        while True:
           future, data = await self.queue.get()
           future.set_result(True)
           self.send(data)
           await asyncio.sleep(flood_rate, loop=self.loop)

    def send(self, data):
        try:
            self.protocol.write(data)
        except AttributeError:
            # Not connected yet
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

    def run(self, forever=True):
        self.create_connection()
        self.add_signal_handlers()

        if forever:
            self.loop.run_forever()
