import on

import util
from util import put, deep_get, deep_set

"""
Room digivice:
1. Adjust lamp power and brightness based on pre-defined modes (default priority 0);
2. Adjust lamp brightness based on the (aggregate) brightness (default priority 1); 
    - brightness is "divided" uniformly across lamps
3. Intent propagation is implemented for the universal lamp's power only.

Mounts:
-  mock.digi.dev/v1/unilamps
-  mock.digi.dev/v1/colorlamps

"""

ul_gvr = "mock.digi.dev/v1/unilamps"
cl_gvr = "mock.digi.dev/v1/colorlamps"

mode_config = {
    "work": {
        "lamps": {
            "power": "on",
            "brightness": 1.0,
            "ambiance_color": "white",
        }
    },
    "sleep": {
        "lamps": {
            "power": "off",
        }
    },
    "idle": {
        "lamps": {
            "brightness": 0.2,
        }
    }
}

lamp_converters = {
    ul_gvr: {
        "power": {
            "from": lambda x: x,
            "to": lambda x: x,
        },
        "brightness": {
            "from": lambda x: x,
            "to": lambda x: x,
        }
    },
    cl_gvr: {
        "power": {
            "from": lambda x: "on" if x == 1 else "off",
            "to": lambda x: 1 if x == "on" else 0,
        },
        "brightness": {
            "from": lambda x: x / 255,
            "to": lambda x: x * 255,
        },
    }
}

# validation
...


# intent back-prop
@on.mount
def h(parent, bp):
    room = parent

    for _, child_path, old, new in bp:
        typ, attr = util.typ_attr_from_child_path(child_path)

        if typ == ul_gvr and attr == "power":
            put(path="control.power.intent",
                src=new, target=room)


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
    room, devices = parent, mounts
    mode = deep_get(room, "control.mode.intent")

    # Handle mode
    matched = True
    if mode is not None:

        # check lamps
        _config = mode_config[mode]["lamps"]
        for lt in [ul_gvr, cl_gvr]:

            # iterate over individual lamp
            for n, _l in devices.get(lt, {}).items():
                if "spec" not in _l:
                    continue
                _l = _l["spec"]

                for attr in ["power", "brightness"]:
                    _convert = lamp_converters[lt][attr]["from"]
                    if attr not in _config:
                        continue
                    if _config[attr] != _convert(
                            deep_get(_l, f"control.{attr}.status")):
                        matched = False
        deep_set(room, f"control.mode.status", mode if matched else "undef")

    # - other devices
    ...

    # Handle brightness
    _bright = 0
    for lt in [ul_gvr, cl_gvr]:
        pc = lamp_converters[lt]["power"]["from"]
        bc = lamp_converters[lt]["brightness"]["from"]

        # iterate over individual lamp
        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue
            _l = _l["spec"]

            _p = deep_get(_l, "control.power.status", "off")
            _b = deep_get(_l, "control.brightness.status", 0)

            if pc(_p) == "on":
                _bright += bc(_b)

    deep_set(room, f"control.bright.status", _bright)


# intent
@on.mount
@on.control("mode")
def h(parent, mounts):
    room, devices = parent, mounts
    mode = deep_get(room, "control.mode.intent")

    if mode is None:
        return

    # TBD use agg brightness for mode

    # handle lamps
    _config = mode_config[mode]["lamps"]
    for lt in [ul_gvr, cl_gvr]:

        # iterate over individual lamp
        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue
            _l = _l["spec"]

            # configure lamp set-points
            for attr in ["power", "brightness"]:
                if attr not in _config:
                    continue

                put(f"control.{attr}.intent",
                    _config[attr], _l,
                    transform=lamp_converters[lt][attr]["to"])

    # other devices
    ...


@on.mount
@on.control("brightness")
def h(parent, mounts):
    room, devices = parent, mounts
    bright = deep_get(room, "control.brightness.intent")
    lamp_count = len(devices.get(ul_gvr, {})) + \
                 len(devices.get(cl_gvr, {}))

    if bright is None or lamp_count == 0:
        return

    # handle lamps

    div = bright / lamp_count

    # set div for each lamp
    for lt in [ul_gvr, cl_gvr]:

        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue

            _l = _l["spec"]

            put("control.brightness.intent", div, _l,
                transform=lamp_converters[lt]["brightness"]["to"])

    # other devices
    ...
