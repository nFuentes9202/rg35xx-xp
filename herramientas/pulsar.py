# uso: python3 pulsar.py right|left|up|down|south|east|north|west|start|select [veces]
import sys, time, evdev
from evdev import ecodes as e
d = evdev.InputDevice("/dev/input/event1")
k = sys.argv[1]; n = int(sys.argv[2]) if len(sys.argv) > 2 else 1
HAT = {"right": (e.ABS_HAT0X, 1), "left": (e.ABS_HAT0X, -1), "down": (e.ABS_HAT0Y, 1), "up": (e.ABS_HAT0Y, -1)}
BTN = {"a": 304, "b": 305, "y": 306, "x": 307, "south": e.BTN_SOUTH, "east": e.BTN_EAST, "north": e.BTN_NORTH, "west": e.BTN_WEST, "start": e.BTN_START, "select": e.BTN_SELECT}
for _ in range(n):
    if k in HAT:
        a, v = HAT[k]; d.write(e.EV_ABS, a, v); d.write(e.EV_SYN, e.SYN_REPORT, 0); time.sleep(0.12); d.write(e.EV_ABS, a, 0); d.write(e.EV_SYN, e.SYN_REPORT, 0)
    else:
        d.write(e.EV_KEY, BTN[k], 1); d.write(e.EV_SYN, e.SYN_REPORT, 0); time.sleep(0.12); d.write(e.EV_KEY, BTN[k], 0); d.write(e.EV_SYN, e.SYN_REPORT, 0)
    time.sleep(0.35)
