import on
import sys
import time
import threading
import random
import os

import util
from util import deep_set, deep_get

"""
Mock scene digilake generates random objects if a url is provided.
"""

_stop_flag = False

auri = {
    "g": os.environ["GROUP"],
    "v": os.environ["VERSION"],
    "r": os.environ["PLURAL"],
    "n": os.environ["NAME"],
    "ns": os.environ["NAMESPACE"],
}


def gen_objects():
    return [
        {
            "human": {
                "x1": 123,
                "x2": 256,
                "w": 50,
                "h": 400,
            }
        },
        {
            "dog": {
                "x1": 64,
                "x2": 128,
                "w": 50,
                "h": 30,
            }
        },
    ]


def detect():
    global _stop_flag
    while True:
        interval = random.randint(0, 10)
        if _stop_flag:
            break

        util.check_gen_and_patch_spec(**auri,
                                      spec={
                                          "data": {
                                              "output": {
                                                  "objects": gen_objects()
                                              }
                                          }
                                      },
                                      gen=sys.maxsize)
        time.sleep(interval)


# intent
@on.data
def h():
    global _stop_flag
    _stop_flag = True

    # do something
    ...

    _stop_flag = False
    t = threading.Thread(target=detect)
    t.start()
