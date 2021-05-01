"""
This is a mock CLI for sending requests for benchmarks.
"""

import time
import pprint as pp
import logging

import kopf
import digi.util as util
from digi.util import patch_spec, get_spec, deep_get

room = ("bench.digi.dev", "v1", "rooms", "room-test", "default")
lamp = ("bench.digi.dev", "v1", "lamps", "lamp-test", "default")
cam = ("bench.digi.dev", "v1", "cams", "cam-test", "default")
scene = ("bench.digi.dev", "v1", "scenes", "scene-test", "default")

ROOM_ORIG_INTENT = 0.8
ROOM_INTENT = 0.1
ROOM_STATUS = 0.1
LAMP_INTENT = 0.1
LAMP_STATUS = 0.1

measure = None

_registry = util.KopfRegistry()
_kwargs = {
    "registry": _registry,
}


def send_request(auri, s: dict):
    global measure

    resp, e = patch_spec(*auri, s)
    if e is not None:
        print(f"bench: encountered error {e} \n {resp}")
        exit()


def benchmark_room_lamp():
    global measure, room, lamp
    measure = dict()
    measure = {
        "start": time.time(),
        "end": None,
        "request": None,
        "fulfill": None,
        "forward_root": None,
        "forward_leaf": None,
        "backward_root": None,
        "backward_leaf": None,
    }

    send_request(room, {
        "control": {
            "brightness": {
                "intent": ROOM_INTENT
            }
        }
    })

    measure["request"] = time.time()

    # wait until results are ready
    while True:
        pp.pprint(measure)
        if all(v is not None for v in measure.values()):
            break
        time.sleep(5)

        room_spec, _, _ = get_spec(*room)
        lamp_spec, _, _ = get_spec(*lamp)

        # XXX simplify this mess
        measure["forward_root"] = deep_get(room_spec, "obs.forward_ts")
        measure["forward_leaf"] = deep_get(lamp_spec, "obs.forward_ts")
        measure["backward_root"] = deep_get(room_spec, "obs.backward_ts")
        measure["backward_leaf"] = deep_get(lamp_spec, "obs.backward_ts")
        measure["fulfill"] = deep_get(room_spec, "obs.backward_ts")
        measure["end"] = deep_get(room_spec, "obs.backward_ts")

    # post proc
    return {
        "rt": measure["request"] - measure["start"],
        "ttf": measure["fulfill"] - measure["forward_root"],
        "fpt": measure["forward_leaf"] - measure["forward_root"],
        "bpt": measure["backward_root"] - measure["backward_leaf"],
        "dt": measure["backward_leaf"] - measure["forward_leaf"],
    }


def benchmark_room_scene():
    # TBD
    pass


def init():
    util.run_operator(_registry, log_level=logging.INFO)

    # assume the digi-graph has
    # been created with the default
    # brightness of the room set to
    # 0.8
    ...


def reset():
    global measure
    measure = None
    send_request(room, {
        "control": {
            "brightness": {
                "intent": ROOM_ORIG_INTENT
            }
        }
    })


if __name__ == '__main__':
    init()
    result = benchmark_room_lamp()
    pp.pprint(result)
