import logging
import serial

class labpc(object):
    def __init__(self, actor, name, logLevel=logging.DEBUG):
        self.name = name
        self.actor = actor
        self.logger = logging.getLogger(self.name)
        self.logger.setLevel(logLevel)
        
        self.url = self.actor.config.get(self.name, 'url')
        self.conn = None

        self.EOL = '\n'
        self.timeout = 15
        
    def start(self):
        pass

    def stop(self):
        pass

    def _connect(self):
        if self.conn is None:
            self.logger.debug('connecting to %s', self.url)
            conn = serial.serial_for_url(self.url,
                                         timeout=self.timeout)
            self.conn = conn

        return self.conn
            
    def sendOneCommand(self, cmdStr, cmd=None):
        conn = self._connect()
        
        self.logger.debug('sending %s', cmdStr)
        conn.write(cmdStr + self.EOL)
        ret = conn.readline()
        self.logger.debug('read %s', ret)

        return ret
