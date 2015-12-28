import sys
import os
import time
import json
import socket
import math

if sys.version_info[0] != 2:
    raise "Must be using Python 2"

class SocketWriter(object):
    def __init__(self, path):
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.connect(path)

    def send(self, payload):
        self.socket.send(json.dumps(payload) + "\n")

if __name__ == "__main__":
    socket_writer = SocketWriter("./comm.sock")
    while True:
        time.sleep(0.01)
        x = math.sin(time.time() / 10.)
        y = x + 1
        payload = (x, y)
        # print json.dumps(payload)
        socket_writer.send(payload)
