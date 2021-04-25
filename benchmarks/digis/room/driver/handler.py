from digi import on, logger
from digi.view import TypeView, DotView


@on.mount
@on.control
def h(proc_view):
    with TypeView(proc_view) as tv, DotView(tv) as dv:
        # logger.info(dv)
        room_brightness = dv.root.control.brightness
        room_brightness.status = 0

        if "lamps" not in dv:
            return

        active_lamps = [l for _, l in dv.lamps.items()
                        if l.control.power.status == "on"]
        for _l in active_lamps:
            room_brightness.status += _l.control.brightness.status
            l.control.brightness.intent = room_brightness.intent / len(active_lamps)
