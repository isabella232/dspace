import sys
import time
import threading
import random
import os

import digi
import digi.on as on
import digi.util as util

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
    return random.choices([
        {
            "human": {
                "x1": random.randint(100, 1000),
                "x2": random.randint(100, 1000),
                "w": random.randint(0, 200),
                "h": random.randint(0, 200),
            }
        },
        {
            "dog": {
                "x1": random.randint(100, 1000),
                "x2": random.randint(100, 1000),
                "w": random.randint(0, 200),
                "h": random.randint(0, 200),
            }
        },
        {
            "roomba": {
                "x1": random.randint(100, 1000),
                "x2": random.randint(100, 1000),
                "w": random.randint(0, 200),
                "h": random.randint(0, 200),
            }
        },
    ], k=random.randint(0, 4))


def detect():
    global _stop_flag
    while True:
        interval = random.randint(5, 60)
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
@on.data("input")
def h():
    global _stop_flag
    _stop_flag = True

    # do something
    ...

    _stop_flag = False
    t = threading.Thread(target=detect)
    t.start()


if __name__ == '__main__':
    digi.run()
