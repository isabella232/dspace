import digi
import digi.on as on

import digi.util as util
from digi.util import put, first_attr, first_type

"""Universal lamp translates power and brightness 
to vendor specific lamps."""

converters = {
    "digi.dev/v1/colorlamps": {
        "power": {
            "from": lambda x: "on" if x == 1 else "off",
            "to": lambda x: 1 if x == "on" else 0,
        },
        "brightness": {
            "from": lambda x: x / 255,
            "to": lambda x: x * 255,
        },
    },
    "digi.dev/v1/geenilamps": {
        "power": {
            "from": lambda x: x,
            "to": lambda x: x,
        },
        "brightness": {
            "from": lambda x: x,
            "to": lambda x: x,
        }
    },
}


# validation
@on.mount
def h(mounts):
    count = util.mount_size(mounts)
    assert count <= 1, \
        f"more than one lamp is mounted: " \
        f"{count}"


# intent back-prop
@on.mount
def h(parent, bp):
    ul = parent

    for _, child_path, old, new in bp:
        typ, attr = util.typ_attr_from_child_path(child_path)

        assert typ in converters, typ

        # back-prop logic
        put(path=f"control.{attr}.intent",
            src=new, target=ul,
            transform=converters[typ][attr]["from"])


# status
@on.mount("lamps")
def h(lp, ul, typ):
    lp = first_attr("spec", lp)

    assert typ in converters, typ

    put(f"control.power.status", lp, ul,
        transform=converters[typ]["power"]["from"])

    put(f"control.brightness.status", lp, ul,
        transform=converters[typ]["brightness"]["from"])


@on.mount("colorlamps")
def h(lp, ul, typ):
    lp = first_attr("spec", lp)

    assert typ in converters, typ

    put(f"control.power.status", lp, ul,
        transform=converters[typ]["power"]["from"])

    put(f"control.brightness.status", lp, ul,
        transform=converters[typ]["brightness"]["from"])


# intent forwarding
@on.mount
@on.control
def h(parent, child):
    ul, lp = parent, first_attr("spec", child)
    if lp is None:
        return

    typ = first_type(child)
    assert typ in converters, typ

    put(f"control.power.intent", ul, lp,
        transform=converters[typ]["power"]["to"])

    put(f"control.brightness.intent", ul, lp,
        transform=converters[typ]["brightness"]["to"])


if __name__ == '__main__':
    digi.run()
