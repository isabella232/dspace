import os, requests
import on


@on.control
def h0(view):
    print("ASDF:", view)
    for k, v in view.items():
        v["status"] = v["intent"]


# @on.control
# def h1(view):
#     view["status"] = view["intent"]

# @on.control("power", priority=1)
# def h1(view):
#     if view["intent"] == view["status"]:
#         return  # skip
#     requests.post(
#         url=os.environ["ENDPOINT"],
#         data={"power": view["intent"]}
#     )
#
#
# @on.control("brightness", priority=0)
# def h2(view):
#     ...
