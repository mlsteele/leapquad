# Leap Quad

Control a quadcopter with a leap.

Hardware:
- [Leap Motion](https://www.leapmotion.com/) Dev Board V.05
- [Crazyflie 2.0](https://www.bitcraze.io/crazyflie-2/)

## Installation

To install the LeapMotion software on linux, install the deb from their developer download site.
If the deb reports an error it may be because it uses upstart but you have systemd.
To fix this, follow the instructions in `leapd.service` to install a systemd unit and run
```shell
sudo service leapd restart
```

Put the LeapSDK directory somewhere and set your `$LEAPSDK` env var to point to it.

Set your `$CRAZYPY` env var to point to crazyflie-clients-python.

## Running

So... Leap is only python 2 compatible, and CrazyFlie is only python 3 compatible. So that's fun.
The two halves of this program communicate over a unix domain socket.

`leap.py` sends control info to `quad.py` which controls the drone.

Leap -> `leap.py` -> `quad.py` -> Quad
