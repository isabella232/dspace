import digi
import digi.on as on

from digi.util import deep_set, deep_get


# status
@on.control
def h(sv, pv):
    for _attr, _ in sv.items():
        deep_set(pv, f"control.{_attr}.status",
                 deep_get(pv, f"control.{_attr}.intent"))


if __name__ == '__main__':
    digi.run()
