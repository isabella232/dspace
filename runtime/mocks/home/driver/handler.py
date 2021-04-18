import digi
import digi.on as on

import digi.util as util
from digi.util import deep_get, deep_set, deep_set_all

"""
The home digivice has the following capabilities:

Handle rooms:
- Mode -> room mode 
- Room obs.objects -> home.objects
"""

room_gvr = "mock.digi.dev/v1/rooms"

mode_config = {
    "normal": {
        "rooms": {
            "mode": -1
        }
    },
    "away": {
        "rooms": {
            "mode": "sleep"
        }
    },
    "work": {
        "rooms": {
            "mode": "work"
        }
    },
    "emergency": {
        ...
    },
}


# validation
@on.attr
def h(parent):
    mode = deep_get(parent, "control.mode.intent")
    if mode is None:
        return
    assert mode in mode_config, f"{mode} undefined"


@on.attr
def h(parent):
    mode = deep_get(parent, "control.mode.intent")
    objects = deep_get(parent, "obs.objects", {})
    if mode == "away" and "human" in objects:
        # TBD: raise a warning
        # TBD: edge trigger by looking at old_view
        ...


# intent back-prop
...


# status
@on.control
def h(sv, mounts):
    # if no mounted devices, set the
    # status to intent
    if util.mount_size(mounts) == 0:
        for _, v in sv.items():
            if "intent" in v:
                v["status"] = v["intent"]


@on.mount
def h(parent, mounts):
    home = parent

    mode = deep_get(home, "control.mode.intent")
    if mode is None:
        return

    objects = dict()

    # handle rooms
    rooms = mounts.get(room_gvr, {})

    # check all room's mode
    _path = "control.mode.status"
    if len(rooms) == 0:
        deep_get(home, _path)
    elif all(deep_get(r, "spec." + _path) ==
             mode_config[mode]["rooms"]["mode"]
             for _, r in rooms.items()):
        deep_set(home, _path, mode)
    elif mode == "normal":
        deep_set(home, _path, "normal")
    else:
        deep_set(home, _path, "undef")

    # check objects in room
    for n, r in rooms.items():
        for o, _ in deep_get(r, "obs.objects", {}).items():
            objects[n] = {"location": n}

    ...

    deep_set(home, "obs.objects", objects)


# intent
@on.mount
@on.control
def h(parent, mounts):
    mode = deep_get(parent, "control.mode.intent")
    if mode is None or mode == "normal":
        return

    # handle rooms
    rooms = mounts.get(room_gvr, {})

    deep_set_all(rooms, "spec.control.mode.intent",
                 mode_config[mode]["rooms"]["mode"])


if __name__ == '__main__':
    digi.run()
