"""
Control a Crazyflie quadcopter with a Leap Motion (your hands!).
"""

# Add Leap library directories to python path.
import os, sys
try:
    sdk_dir = os.environ["LEAPSDK"]
except KeyError:
    print("Set $LEAPSDK to point to the LeapSDK directory.")
    sys.exit(-1)
arch_dir = "lib/x64" if sys.maxsize > 2**32 else "lib/x86"
sys.path.insert(0, os.path.abspath(os.path.join(sdk_dir, "lib/")))
sys.path.insert(0, os.path.abspath(os.path.join(sdk_dir, arch_dir)))

import Leap
import time
import socket
from socksend import SocketWriter


class LeapRemote(object):
    """Remote control using input from the leap.

    Args:
        safety_timeout: How long without input until the safety engages.
    """
    def __init__(self, safety_timeout=0.5):
        self.controller = Leap.Controller()

        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.thrust = 0

        self.safety_timeout = safety_timeout
        self.t_last_observe = 0

    def zero(self):
        self.roll = 0
        self.pitch = 0
        self.yaw = 0
        self.thrust = 0

    def get_vector(self):
        """Get the control vector.

        Returns: (roll, pitch, yaw, thrust)
            Roll is in radians.
            Pitch is in radians.
            Yaw is in radians.
            Thrust is a float in [0, inf)
                1.0 is pretty fast.
        """
        frame = self.controller.frame()
        hand = frame.hands.rightmost

        if not hand.is_valid:
            # Non-useful frame.
            if time.time() - self.t_last_observe > self.safety_timeout:
                self.zero()
            return (self.roll, self.pitch, self.yaw, self.thrust)

        self.t_last_observe = time.time()
        direction = hand.direction
        self.roll = -hand.palm_normal.roll
        self.pitch = -direction.pitch
        self.yaw = direction.yaw
        self.thrust = max(0, map_linear(hand.palm_position.y,
                                        210, 600, 0, 1.0))
        return (self.roll, self.pitch, self.yaw, self.thrust)


def map_linear(x, in_min, in_max, out_min, out_max):
    """Transform a value from one space to another."""
    return (x - in_min) * (out_max - out_min) / float(in_max - in_min) + out_min;


def interact():
    """Drop to an interactive REPL."""
    import code, inspect
    frame = inspect.currentframe()
    prevlocals = frame.f_back.f_locals
    replvars = globals().copy()
    replvars.update(prevlocals)
    code.InteractiveConsole(locals=replvars).interact()


if __name__ == "__main__":
    remote = LeapRemote()
    try:
        socket_writer = SocketWriter("./comm.sock")
    except socket.error:
        print "Start quad.py first."
        sys.exit(-1)
    while True:
        time.sleep(0.01)
        vector = remote.get_vector()
        print "\t".join(map("{:.2f}".format, vector))
        socket_writer.send(vector)
