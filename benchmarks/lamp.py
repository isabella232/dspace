"""
This is a mock CLI for sending requests for benchmarks.
"""

import time
import pprint as pp
import logging

import digi.util as util
from digi.util import patch_spec, get_spec, deep_get

lamp_gvr = ("bench.digi.dev", "v1", "lamps", "lamp-test", "default")
measure_gvr = ("bench.digi.dev", "v1", "measures", "measure-test", "default")

LAMP_ORIG_INTENT = 0.8
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


def benchmark_lamp(root_intent=LAMP_INTENT, skip_result=False):
    global measure
    measure = dict()
    measure = {
        "start": time.time(),
        # "request": None,
        # "forward_root": None,
        # "backward_root": None,
        "forward_leaf": None,
        "backward_leaf": None,
    }

    send_request(lamp_gvr, {
        "control": {
            "brightness": {
                "intent": root_intent
            }
        }
    })

    if skip_result:
        return {}

    # wait until results are ready
    while True:
        if all(v is not None and v > 0 for k, v in measure.items()):
            break

        measure_spec, _, _ = get_spec(*measure_gvr)
        measure.update(measure_spec["obs"])
    now = time.time()
    pp.pprint(measure)
    # post proc
    return {
        "ttf": now - measure["start"],
        "fpt": measure["forward_leaf"] - measure["start"],
        "bpt": now - measure["backward_leaf"],
        "dt": measure["backward_leaf"] - measure["forward_leaf"],
    }


def reset():
    global measure
    measure = None

    send_request(measure_gvr, {
        "obs": {
            # "forward_root": -1,
            # "backward_root": -1,
            "forward_leaf": -1,
            "backward_leaf": -1,
        }
    })


if __name__ == '__main__':
    # warm-up
    benchmark_lamp(root_intent=0.5, skip_result=True)
    print("warmed up")
    reset()

    time.sleep(5)
    result = benchmark_lamp(root_intent=LAMP_INTENT)
    pp.pprint(result)
