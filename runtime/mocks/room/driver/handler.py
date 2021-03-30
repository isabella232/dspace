import on

from util import put, deep_get, deep_set

"""
Room digivice:
1. Adjust lamp power and brightness based on pre-defined modes (default priority 0);
2. Adjust lamp brightness based on the (aggregate) brightness (default priority 1); 
    - brightness is "divided" uniformly across lamps

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
            "brightness": 0.0,
            "ambiance_color": "blue",
        }
    },
    "idle": {
        "lamps": {
            "power": "on",
            "brightness": 0.2,
            "ambiance_color": "yellow",
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
def h():
    pass


# status
@on.mount
def h(parent, mounts):
    room, devices = parent, mounts
    mode = deep_get(room, "control.mode.intent")
    bright = deep_get(room, "control.brightness.intent")

    # Handle mode
    if mode is not None:

        # check lamps
        for lt in [ul_gvr, cl_gvr]:

            # iterate over individual lamp
            for n, _l in devices.get(lt, {}).items():
                if "spec" not in _l:
                    continue
                _l = _l["spec"]

                matched = True
                for attr in ["power", "brightness"]:
                    convert = lamp_converters[lt][attr]["from"]
                    if mode_config[mode]["lamps"][attr] != \
                            convert(deep_get(_l, f"control.{attr}.intent")):
                        matched = False
                deep_set(room, f"control.mode.status", mode if matched else "undef")

    # - other devices
    ...

    # Handle brightness
    # - check lamps


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
    for lt in [ul_gvr, cl_gvr]:

        # iterate over individual lamp
        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue
            _l = _l["spec"]

            # configure lamp set-points
            for attr in ["power", "brightness"]:
                put(f"control.{attr}.intent",
                    mode_config[mode]["lamps"][attr], _l,
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
