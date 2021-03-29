import on

from util import put, first_type, first_attr, full_gvr

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

# validation
...


# intent back-prop
@on.mount
def h():
    pass


# # status
@on.mount
def h(parent, mounts):
    pass


# intent
@on.mount
@on.control("mode")
def h(parent, mounts):
    room, devices = parent, mounts
    mode = room["control"]["mode"]["intent"]

    # handle lamps
    for lt, power_cnv in [(ul_gvr, lambda x: x),
                          (cl_gvr, lambda x: 1 if x == "on" else 0)]:

        # iterate over individual lamp
        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue

            _l = _l["spec"]

            # set lamp power
            put("control.power.intent",
                mode_config[mode]["lamps"]["power"], _l,
                transform=power_cnv)
    
    # other devices
    ...


@on.mount
@on.control("brightness")
def h(parent, mounts):
    room, devices = parent, mounts
    bright = room["control"]["brightness"]["intent"]

    # handle lamps
    lamp_count = len(devices.get(ul_gvr, {})) + \
                 len(devices.get(cl_gvr, {}))

    if lamp_count == 0:
        return

    div = bright / lamp_count

    # set div for each lamp
    for lt, bright_cnv in [(ul_gvr, lambda x: x),
                           (cl_gvr, lambda x: x * 255)]:

        for n, _l in devices.get(lt, {}).items():
            if "spec" not in _l:
                continue

            _l = _l["spec"]

            put("control.brightness.intent", div, _l,
                transform=bright_cnv)

    # other devices
    ...
