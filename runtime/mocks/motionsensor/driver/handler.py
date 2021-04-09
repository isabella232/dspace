import on
import sys
import time
import threading
import random
import os

import util

"""Motion sensor mock digivice generates random motion 
events based on sensitivity."""

_stop_flag = False

_g, _v, _r = os.environ["GROUP"], os.environ["VERSION"], os.environ["PLURAL"]
_n, _ns = os.environ["NAME"], os.environ["NAMESPACE"]


def trigger(sty):
    global _stop_flag
    while True:
        interval = random.randint(0, sty * 60)
        time.sleep(interval)
        if _stop_flag:
            break
        _set()


def _set():
    util.check_gen_and_patch_spec(_g, _v, _r,
                                  _n, _ns,
                                  {
                                      "obs": {
                                          "last_triggered_time": str(time.time())
                                      }
                                  },
                                  sys.maxsize)


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
