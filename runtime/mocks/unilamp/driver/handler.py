import os

import on
from util import put, first_attr, first_type

"""Universal lamp translates power and brightness 
to vendor specific lamps."""


# validation
@on.mount
def h(lamp_types):
    count = 0
    for typ, lamps in lamp_types.items():
        count += len(lamps)
    assert count <= 1, \
        f"more than one lamp is mounted: " \
        f"{count}"


# status
@on.mount("lamps")
def h(lp, ul):
    lp = first_attr("spec", lp)

    put("control.power.status", lp, ul)

    put("control.brightness.status", lp, ul)


@on.mount("colorlamps")
def h(lp, ul):
    lp = first_attr("spec", lp)

    put("control.power.status", lp, ul,
        transform=lambda x: "on" if x == 1 else "off")

    put("control.brightness.status", lp, ul,
        transform=lambda x: x / 255)


# intent
@on.mount
@on.control
def h(parent, child):
    ul, lp = parent, first_attr("spec", child)
    lt = first_type(child)

    if lt == _gvr("lamps"):
        put("control.power.intent", ul, lp)

        put("control.brightness.intent", ul, lp)

    elif lt == _gvr("colorlamps"):
        put("control.power.intent", ul, lp,
            transform=lambda x: 1 if x == "on" else 0)

        put("control.brightness.intent", ul, lp,
            transform=lambda x: x * 255)

    # more lamps
    ...


def _gvr(s):
    if len(s.split("/")) == 1:
        return "/".join([os.environ["GROUP"],
                         os.environ["VERSION"],
                         s])
    else:
        return s
