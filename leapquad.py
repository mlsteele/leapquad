"""
Control a Crazyflie quadcopter with a Leap Motion (your hands!).
"""

# Add Leap library directories to python path.
import os, sys
try:
    sdk_dir = os.environ["LEAPSDK"]
except KeyError:
    print "Set $LEAPSDK to point to the LeapSDK directory."
    sys.exit(-1)
arch_dir = "lib/x64" if sys.maxsize > 2**32 else "lib/x86"
sys.path.insert(0, os.path.abspath(os.path.join(sdk_dir, "lib/")))
sys.path.insert(0, os.path.abspath(os.path.join(sdk_dir, arch_dir)))

# Add CrazyFlie library directories to python path.
import os, sys
try:
    cfclients_dir = os.environ["CRAZYPY"]
except KeyError:
    print "Set $CRAZYPY to point to the crazyflie-clients-python directory."
    sys.exit(-1)
sys.path.insert(0, os.path.abspath(os.path.join(cfclients_dir, "lib/")))

import Leap, sys, thread, time
import cflib
from cflib.crazyflie import Crazyflie

logging.basicConfig(level=logging.ERROR)


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
        self.roll = hand.palm_normal.roll
        self.pitch = direction.pitch
        self.yaw = direction.yaw
        self.thrust = max(0, map_linear(hand.palm_position.y,
                                        300, 470, 0, 1.0))
        return (self.roll, self.pitch, self.yaw, self.thrust)


class QuadController(object):
    """Connects to a Crazyflie and controls from the leap."""
    def __init__(self, link_uri, remote):
        self.remote = remote
        self._cf = Crazyflie()
        self._cf.connected.add_callback(self._connected)
        self._cf.disconnected.add_callback(self._disconnected)
        self._cf.connection_failed.add_callback(self._connection_failed)
        self._cf.connection_lost.add_callback(self._connection_lost)
        self._cf.open_link(link_uri)
        print("Connecting to %s" % link_uri)

    def _connected(self, link_uri):
        """ This callback is called form the Crazyflie API when a Crazyflie
        has been connected and the TOCs have been downloaded."""
        try:
            self._run()
        except Exception as ex:
            print("Run method raised an exception. Shutting down.")
            traceback.print_exc()
        finally:
            # Make sure that the last packet leaves before the link is closed
            # since the message queue is not flushed before closing
            self._cf.commander.send_setpoint(0, 0, 0, 0)
            time.sleep(0.1)
            self._cf.close_link()

    def _connection_failed(self, link_uri, msg):
        """Callback when connection initial connection fails (i.e no Crazyflie
        at the specified address)"""
        print("Connection to %s failed: %s" % (link_uri, msg))

    def _connection_lost(self, link_uri, msg):
        """Callback when disconnected after a connection has been made (i.e
        Crazyflie moves out of range)"""
        print("Connection to %s lost: %s" % (link_uri, msg))

    def _disconnected(self, link_uri):
        """Callback when the Crazyflie is disconnected (called in all cases)"""
        print("Disconnected from %s" % link_uri)

    def _run(self):
        # Unlock startup thrust protection
        self._cf.commander.send_setpoint(0, 0, 0, 0)

        while True:
            rroll, rpitch, ryaw, rthrust = self.remote.get_vector()
            roll = int(rroll * 10)
            pitch = int(rpitch * 10)
            yaw = int(ryaw * 10)
            thrust = int(map_linear(rthrust, 0, 1.0, 0, 65000))
            self._cf.commander.send_setpoint(roll, pitch, yaw, thrust)

    def _tween(self, start, end, x):
        """A value goes from start to end and x is in [0,1]"""
        x = float(x)
        return start + (end - start) * x


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


def scan_for_crazyflies():
    # Scan for Crazyflies and use the first one found
    print("Scanning interfaces for Crazyflies...")
    available = cflib.crtp.scan_interfaces()
    print("Crazyflies found:")
    for i in available:
        print(i[0])

    if len(available) > 0:
        return available[0][0]
    else:
        print("No Crazyflies found")
        return None


if __name__ == "__main__":
    # Initialize the low-level drivers (don't list the debug drivers)
    cflib.crtp.init_drivers(enable_debug_driver=False)

    # scan_for_crazyflies()

    radio = "radio://0/80/250K"
    remote = LeapRemote()
    qc = QuadController(radio, remote)

    # while True:
    #     time.sleep(0.01)
    #     vector = remote.get_vector()
    #     print "\t".join(map("{:.2f}".format, vector))
