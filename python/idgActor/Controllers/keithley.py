import socket
import logging
import io
import serial
import socket

from ics.utils.tcp import bufferedSocket

class keithley(object):
    def __init__(self, actor, name, logLevel=logging.DEBUG):
        self.name = name
        self.actor = actor
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logLevel)

        self.url = self.actor.config.get(self.name, 'url')
        _, parts = self.address = self.url.split('://')
        parts = parts.split(':')
        self.address = (parts[0], int(parts[1]))
        self.conn = None
        self.io = bufferedSocket.BufferedSocket(self.name+"IO", EOL='\r')
        self.EOL = '\n'
        self.timeout = 5

    def start(self, cmd):
        cmd.debug(f'text="starting commander {self.name}"')

    def stop(self, cmd):
        cmd.debug(f'text="stopping commander {self.name}"')

    def _connect(self):
        if self.conn is None:
            self.logger.debug('connecting to %s or %s', self.url, self.address)
            #conn = serial.serial_for_url(self.url,
            #                             timeout=self.timeout)
            #self.conn = conn
            self.conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.conn.connect(self.address)

            # buffer = io.BufferedRandom(conn)
            #buffer = io.BufferedRWPair(conn, conn)
            #self.io = io.TextIOWrapper(buffer,
            #                           encoding='latin-1',
            #                           newline='\r',
            #                           line_buffering=True)
        return self.conn

    def XXreadOneLine(self, conn, cmd=None):
        buf = []
        while True:
            c = conn.read(1)
            cmd.debug(f'text="read: {c}"')
            buf = buf + c
            if c in '\r\n':
                return buf

    def sendOneCommand(self, cmdStr, cmd=None, noResponse=False):
        conn = self._connect()

        if cmd is not None:
            cmd.debug(f'text="sending {cmdStr}"')
        self.logger.debug('sending %s', cmdStr)
        conn.sendall((cmdStr + self.EOL).encode('latin-1'))
        if noResponse:
            return None

        # conn.flush()
        ret = self.io.getOneResponse(sock=conn, timeout=2, cmd=cmd)
        # ret = conn.readline()
        ret = ret.strip()
        if cmd is not None:
            cmd.debug(f'text="received {ret}"')
        self.logger.debug('read %s', ret)

        return ret
