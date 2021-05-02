import time

import digi
from digi import on, logger
from digi.view import TypeView, DotView
from digi.util import deep_get, deep_set, patch_spec

_measure = ("bench.digi.dev", "v1", "measures", "measure-test", "default")
_forward_set = False
_backward_set = False


@on.mount
@on.control
def h(proc_view):
    with TypeView(proc_view) as tv, DotView(tv) as dv:
        room_brightness = dv.root.control.brightness
        room_brightness.status = 0

        if "lamps" not in dv:
            return

        active_lamps = [l for _, l in dv.lamps.items()
                        if l.control.power.status == "on"]
        for _l in active_lamps:
            room_brightness.status += _l.control.brightness.status
            _l.control.brightness.intent = room_brightness.intent / len(active_lamps)

    # # benchmark
    # global _forward_set
    # if deep_get(proc_view, "control.brightness.intent") == 0.1 and not _forward_set:
    #     resp, e = patch_spec(*_measure, {
    #         "obs": {
    #             "forward_root": time.time()
    #         }
    #     })
    #     if e is None:
    #         _forward_set = True
    #
    # global _backward_set
    # if deep_get(proc_view, "control.brightness.status") == 0.1:
    #     resp, e = patch_spec(*_measure, {
    #         "obs": {
    #             "backward_root": time.time()
    #         }
    #     })
    #     _backward_set = True


if __name__ == '__main__':
    digi.run()
