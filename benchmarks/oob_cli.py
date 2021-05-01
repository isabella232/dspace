"""
This is a mock CLI for sending requests for benchmarks.
"""

import time
import pprint as pp
import logging

import kopf
import digi.util as util
from digi.util import patch_spec

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


@kopf.on.update(*room[:3], **_kwargs)
def h_room(spec, *args, **kwargs):
    global measure
    _, _ = args, kwargs

    b = spec["control"]["brightness"]
    if b["intent"] == ROOM_INTENT:
        measure["forward_root"] = time.time()

    if b["status"] == ROOM_STATUS:
        _t = time.time()
        measure["backward_root"] = _t
        measure["fulfill"] = _t
        measure["end"] = _t


@kopf.on.update(*lamp[:3], **_kwargs)
def h_lamp(spec, *args, **kwargs):
    global measure
    _, _ = args, kwargs

    b = spec["control"]["brightness"]
    if b["intent"] == LAMP_INTENT:
        measure["forward_leaf"] = time.time()

    if b["status"] == LAMP_STATUS:
        measure["backward_leaf"] = time.time()


@kopf.on.update(*cam[:3], **_kwargs)
def h_cam(spec, *args, **kwargs):
    global measure
    _, _ = args, kwargs


@kopf.on.update(*scene[:3], **_kwargs)
def h_scene(spec, *args, **kwargs):
    global measure
    _, _ = args, kwargs


def benchmark_room_lamp():
    global measure
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
                "intent": ROOM_STATUS
            }
        }
    })

    measure["request"] = time.time()

    # wait until results are ready
    while True:
        pp.pprint(measure)
        time.sleep(5)
        if all(v is not None for v in measure.values()):
            break

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
