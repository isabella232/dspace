import digi
import digi.on as on
from digi import logger
from digi.util import deep_get

import digi.reconcile as rc

import time
import threading
import lifx


def _poll_and_update(id_):
    pass


dev = None


# status
@on.meta
def h0(sv):
    e = sv.get("endpoint", None)
    if e is None:
        return

    global dev
    dev = lifx.discover(e)
    # convert
    # _t = threading.Thread(target=_poll_and_update,
    #                       args=(e,))

    # t1.start()
    # t1.join()


# intent
@on.control
def h1(sv):
    p, b = deep_get(sv, "power.intent"), \
           deep_get(sv, "brightness.intent")
    # convert
    status = lifx.get(dev)
    logger.info(status)


if __name__ == '__main__':
    digi.run()
