import sys
import os
import time
import json
import socket

READ_DEFAULT_NONE = {"implementation": "detail"}

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

class SocketReader(object):
    def __init__(self, path):
        self.path = path
        self._reup()

    def _reup(self):
        if os.path.exists(self.path):
            os.remove(self.path)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(self.path)
        self.socket.settimeout(0.5)
        self.file = self.socket.makefile("r")

    def read(self, default=READ_DEFAULT_NONE):
        if default is READ_DEFAULT_NONE:
            return json.loads(self.file.readline())
        else:
            try:
                return json.loads(self.file.readline())
            except socket.timeout:
                self._reup()
                return default

if __name__ == "__main__":
    socket_reader = SocketReader("./comm.sock")
    while True:
        print(socket_reader.read(default=0))
