import asyncio


class IrcProtocol(asyncio.Protocol):
    def __init__(self, factory):
        self.factory = factory
        self.encoding = factory.encoding
        self.transport = None
        self.closed = True

    def connection_made(self, transport):
        self.transport = transport
        self.closed = False

    def decode(self, data):
        return data.decode(self.encoding, 'ignore')

    def data_received(self, data):
        data = self.decode(data)
        for line in data.split('\r\n')[:-1]:
            self.factory.process_data(line)

    def encode(self, data):
        if isinstance(data, str):
            data = data.encode(self.encoding)
        return data

    def write(self, data):
        if data is not None:
            data = self.encode(data)
            if not data.endswith(b'\r\n'):
                data = data + b'\r\n'
            self.transport.write(data)

    def connection_lost(self, exc):
        self.factory.notify('connection_lost')
        if not self.closed:
            self.close()
            self.factory.loop.call_later(2, self.factory.create_connection)

    def close(self):
        if not self.closed:
            try:
                self.transport.close()
            finally:
                self.closed = True
