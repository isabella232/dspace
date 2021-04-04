import on

"""
The room digivice implements the following logic:

Handle lamps:
- Mode -> lamp power
- Brightness -> lamp brightness

...
"""


@on.attr
def h_status(view):
    mounts = view["mount"]

    view["status"] = "idle"

# @on.control("mode")
# def h1(view):
#     view["status"] = "idle"

# @on.mount("lamps")
# @on.control("mode", priority=1)
# def h1(view):
#     if view["mode"]["intent"] == "sleep":
#         for l in view["lamps"]:
#             l["power"]["intent"] = "off"
#     # set view["mode"]["status"]
#     ...
#
# @on.mount("lamps")
# @on.control("brightness", priority=0)
# def h2(view):
#     for l in view["lamps"]:
#         l["power"]["intent"] = "on"
#         l["brightness"]["intent"] \
#             = view["brightness"]["intent"]
#     ...
#
# @on.mount("lamps")
# def handle_lamps(view):
#     for n, l in view.items():
#         if view["control"][""]
#     ...
#
# @on.mount("speakers")
# def handle_speakers(view):
#     ...
