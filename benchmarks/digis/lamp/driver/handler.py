import digi
import digi.on as on
from digi import logger
from digi.util import deep_get, patch_spec, deep_set

import time
import threading
import lifx

_poll = None
_dev = None

# source: https://github.com/mclarkk/lifxlan
# power can be "on"/"off", True/False, 0/1, or 0/65535
# color is a HSBK list of values: [hue (0-65535), saturation (0-65535), brightness (0-65535), Kelvin (2500-9000)]
# duration is the transition time in milliseconds
# rapid is True/False. If True, don't wait for successful confirmation, just send multiple packets and move on
# is_transient is 1/0. If 1, return to the original color after the specified number of cycles. If 0,
# set light to specified color
# period is the length of one cycle in milliseconds
# cycles is the number of times to repeat the waveform
# duty_cycle is an integer between -32768 and 32767. Its effect is most obvious with the Pulse waveform
#     set duty_cycle to 0 to spend an equal amount of time on the original color and the new color
#     set duty_cycle to positive to spend more time on the original color
#     set duty_cycle to negative to spend more time on the new color
# waveform can be 0 = Saw, 1 = Sine, 2 = HalfSine, 3 = Triangle, 4 = Pulse (strobe)
# infrared_brightness (0-65535) - is the maximum infrared brightness when the lamp automatically
# turns on infrared (0 = off)
convert = {
    "power": {
        "from": lambda x: "on" if x > 0 else "off",
        "to": lambda x: 65535 if x == "on" else 0,
    },
    "brightness": {
        "from": lambda x: round(x / 65535, 2),
        "to": lambda x: x * 65535,
    }
}


class _Poll(threading.Thread):
    def __init__(self, dev, interval=0.1, backward_value=0):
        threading.Thread.__init__(self)
        self.dev = dev
        self.interval = interval
        self.stop_flag = False

        # benchmark
        self.backward_value = backward_value
        self._observed_backward = False

    def run(self):
        while True:
            if self.stop_flag:
                break

            status = lifx.get(self.dev)
            if status is None:
                continue
            p, b = status.get("power", {}), status.get("color", {})[2]
            p, b = convert["power"]["from"](p), convert["brightness"]["from"](b)

            patch = {
                "control": {
                    "power": {
                        "status": p,
                    },
                    "brightness": {
                        "status": b,
                    },
                }
            }

            # benchmark
            if b == self.backward_value and not self._observed_backward:
                deep_set(patch, "obs.backward_ts", time.time(), create=True)
                self._observed_backward = True

            resp, e = patch_spec(*digi.auri, patch)
            if e is not None:
                logger.error(f"unable to update status {e}")

            time.sleep(self.interval)


# status
@on.meta
def h0(sv, pv):
    e = sv.get("endpoint", None)
    if e is None:
        return

    global _dev
    for _ in range(sv.get("discover_retry", 3)):
        _dev = lifx.discover(e)
        if _dev is not None:
            break

    if _dev is None:
        return

    if _poll is not None:
        _poll.stop_flag = True

    _p = _Poll(dev=_dev,
               interval=sv.get("poll_interval", 0.5),
               backward_value=deep_get(pv, "meta.backward_value"))
    _p.start()


# intent
@on.control
def h1(sv, pv):
    global _dev
    if _dev is None:
        return

    status = lifx.get(_dev)
    power = status.get("power", 0)
    color = list(status.get("color", [1, 1, 1, 1]))

    p, b = deep_get(sv, "power.intent"), deep_get(sv, "brightness.intent")

    if p is not None:
        power = convert["power"]["to"](p)
    if b is not None:
        color[2] = convert["brightness"]["to"](b)

    # benchmark
    logger.info(f"DEBUG: {b} {pv}")
    if b == pv["meta"]["forward_value"] and deep_get(pv, "obs.forward_ts") is None:
        deep_set(pv, "obs.forward_ts", time.time(), create=True)

    lifx.put(_dev, power, color)


if __name__ == '__main__':
    digi.run()
