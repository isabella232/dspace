import os

import on

"""Universal lamp translates power and brightness 
to vendor specific lamps."""


# validation handlers
@on.mount
def h(lamp_types):
    count = 0
    for typ, lamps in lamp_types.items():
        count += len(lamps)
    assert count <= 1, \
        f"more than one lamp is mounted: " \
        f"{count}"


# status handlers
@on.mount("lamps")
def h(lp, ul):
    lp = _first_attr("spec", lp)

    _set("control.power.status", lp, ul)

    _set("control.brightness.status", lp, ul)


@on.mount("colorlamps")
def h(lp, ul):
    lp = _first_attr("spec", lp)

    _set("control.power.status", lp, ul,
         transform=lambda x: "on" if x == 1 else "off")

    _set("control.brightness.status", lp, ul,
         transform=lambda x: x / 255)


# intent handlers
@on.mount
@on.control
def h(parent, child):
    ul, lp = parent, _first_attr("spec", child)
    lt = _first_type(child)

    if lt == _gvr("lamps"):
        _set("control.power.intent", ul, lp)

        _set("control.brightness.intent", ul, lp)

    elif lt == _gvr("colorlamps"):
        _set("control.power.intent", ul, lp,
             transform=lambda x: 1 if x == "on" else 0)

        _set("control.brightness.intent", ul, lp,
             transform=lambda x: x * 255)

    # more lamps
    ...


# utils
def _set(path, src, target, transform=lambda x: x):
    if type(target) is not dict:
        return

    ps = path.split(".")
    for p in ps[:-1]:
        if p not in target:
            return
        target = target[p]

    if type(src) is not dict:
        target[ps[-1]] = src
        return

    for p in ps[:-1]:
        if p not in src:
            return
        src = src[p]
    target[ps[-1]] = transform(src[ps[-1]])


def _first_attr(attr, d: dict):
    if type(d) is not dict:
        return None
    if attr in d:
        return d[attr]
    for k, v in d.items():
        v = _first_attr(attr, v)
        if v is not None:
            return v
    return None


def _first_type(mounts):
    if type(mounts) is not dict or len(mounts) == 0:
        return None
    return list(mounts.keys())[0]


def _gvr(s):
    if len(s.split("/")) == 1:
        return "/".join([os.environ["GROUP"],
                         os.environ["VERSION"],
                         s])
    else:
        return s
