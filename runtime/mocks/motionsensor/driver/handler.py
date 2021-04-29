import sys
import time
import threading
import random
import os

import digi
import digi.on as on
import digi.util as util
from digi.util import deep_set

"""Motion sensor mock digivice generates random motion 
events based on sensitivity."""

_stop_flag = False

auri = {
    "g": os.environ["GROUP"],
    "v": os.environ["VERSION"],
    "r": os.environ["PLURAL"],
    "n": os.environ["NAME"],
    "ns": os.environ["NAMESPACE"],
}


# TBD: do not use a global _stop_flag
def trigger(sty):
    global _stop_flag
    while True:
        interval = random.randint(0, 60 / sty)
        time.sleep(interval)
        if _stop_flag:
            break

        util.check_gen_and_patch_spec(**auri,
                                      spec={
                                          "obs": {
                                              "last_triggered_time": time.time()
                                          }
                                      },
                                      gen=sys.maxsize)


@on.attr
def h(pv):
    deep_set(pv, "obs.battery_level", "100%", create=True)


# intent
@on.control("sensitivity")
def h(sv):
    global _stop_flag
    _stop_flag = True

    sty = sv.get("intent", 1)
    sty = max(0, min(sty, 100))
    sv["status"] = sty

    _stop_flag = False
    t = threading.Thread(target=trigger,
                         args=(sty,))
    t.start()


if __name__ == '__main__':
    digi.run()
