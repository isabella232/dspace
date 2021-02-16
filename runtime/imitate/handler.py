from typing import Dict

import kopf
import util
from util import KopfRegistry
from imitator import Imitator, get_builder

_init_registry = KopfRegistry()
_imitators: Dict[str, Imitator] = dict()

""" 
Init actor handlers. 

Imitators are created as child actors; each has
its own handlers registered in a separate kopf operator.
"""

_init_config = {
    "group": "digi.dev",
    "version": "v1",
    "plural": "imitates",
    "registry": _init_registry,
}


@kopf.on.create(**_init_config)
def create_imt(**kwargs):
    return {"message": f"on create: {new(**kwargs)}"}


@kopf.on.update(**_init_config)
def update_imt(**kwargs):
    # TBD unregister first or incremental imitator update
    return {"message": f"on update: {new(**kwargs)}"}


@kopf.on.delete(**_init_config, optional=True)
def delete_imt(**kwargs):
    return {"message": f"on delete: {delete(**kwargs)}"}


def new(name, namespace, spec, **kwargs) -> str:
    _ = kwargs

    obs_attrs = list()
    act_attrs = list()

    for o in spec.get("obs"):
        au = util.parse_auri(o)
        if au is None:
            return f"invalid auri {au}"

        obs_attrs.append(au)

    for a in spec.get("action"):
        au = util.parse_auri(a)
        if au is None:
            return f"invalid auri {au}"

        act_attrs.append(au)

    sgy = spec.get("strategy", "naive")
    imt_build = get_builder(sgy)
    if imt_build is None:
        return f"invalid strategy {sgy}"

    sn = util.spaced_name(name, namespace)
    imt = imt_build(name=sn)
    imt.spawn(obs_attrs, act_attrs)
    imt.start()

    _imitators[sn] = imt

    return f"started imitator {sn}"


def delete(name, namespace, **kwargs):
    _ = kwargs

    sn = util.spaced_name(name, namespace)
    imt = _imitators.get(sn)
    if imt is not None:
        imt.stop()
        _imitators.pop(sn, None)
    return f"deleted imitator {sn}"


def main():
    print(f"Starting the main operator.")
    _, _ = util.run_operator(_init_registry)
    print("Created main operator thread.")


if __name__ == "__main__":
    main()
