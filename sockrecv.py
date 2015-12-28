import sys
import os
import time
import json
import socket

if sys.version_info[0] < 3:
    raise Exception("Must be using Python 3")

class SocketReader(object):
    def __init__(self, path):
        if os.path.exists(path):
            os.remove(path)
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(path)
        self.file = self.socket.makefile("r")

    def read(self):
        return json.loads(self.file.readline())

if __name__ == "__main__":
    socket_reader = SocketReader("./comm.sock")
    while True:
        print(socket_reader.read())
