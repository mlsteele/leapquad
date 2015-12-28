"""
Control a Crazyflie quadcopter with a Leap Motion (your hands!).
"""

# Add CrazyFlie library directories to python path.
import os, sys
try:
    cfclients_dir = os.environ["CRAZYPY"]
except KeyError:
    print("Set $CRAZYPY to point to the crazyflie-clients-python directory.")
    sys.exit(-1)
sys.path.insert(0, os.path.abspath(os.path.join(cfclients_dir, "lib/")))

import logging
import cflib
from cflib.crazyflie import Crazyflie

logging.basicConfig(level=logging.ERROR)


class QuadController(object):
    """Connects to a Crazyflie and controls from the leap."""
    def __init__(self, link_uri):
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
    qc = QuadController(radio)
