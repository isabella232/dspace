"""
This is a mock CLI for sending requests for benchmarks.
"""

import time
import pprint as pp
import logging

import kopf
import digi.util as util
from digi.util import patch_spec, get_spec, deep_get

room_gvr = ("bench.digi.dev", "v1", "rooms", "room-test", "default")
measure_gvr = ("bench.digi.dev", "v1", "measures", "measure-test", "default")

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
    global measure
    measure = dict()
    measure = {
        "start": time.time(),
        "request": None,
        "forward_root": None,
        "forward_leaf": None,
        "backward_root": None,
        "backward_leaf": None,
    }

    send_request(room_gvr, {
        "control": {
            "brightness": {
                "intent": ROOM_INTENT
            }
        }
    })

    measure["request"] = time.time()

    # wait until results are ready
    while True:
        if all(v is not None and v > 0 for v in measure.values()):
            break

        measure_spec, _, _ = get_spec(*measure_gvr)
        measure.update(measure_spec["obs"])
        pp.pprint(measure)

        time.sleep(3)

    # post proc
    return {
        "rt": measure["request"] - measure["start"],
        "ttf": measure["backward_root"] - measure["forward_root"],
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
    send_request(room_gvr, {
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
