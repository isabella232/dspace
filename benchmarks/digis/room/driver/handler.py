import time

import digi
from digi import on, logger
from digi.view import TypeView, DotView
from digi.util import deep_get, deep_set


@on.mount
@on.control
def h(proc_view):
    # benchmark
    if deep_get(proc_view, "control.brightness.intent") \
            == deep_get(proc_view, "meta.forward_value", "") \
            and deep_get(proc_view, "obs.forward_ts") is None:
        deep_set(proc_view, "obs.forward_ts", time.time(), create=True)

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

    # benchmark
    if deep_get(proc_view, "control.brightness.status") \
            == deep_get(proc_view, "meta.backward_value", "") \
            and deep_get(proc_view, "obs.backward_ts") is None:
        deep_set(proc_view, "obs.backward_ts", time.time(), create=True)


if __name__ == '__main__':
    digi.run()
