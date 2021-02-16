from typing import Dict, List
from collections import defaultdict

import kopf
import util
from util import Auri, Attr, KopfRegistry

_init_registry = KopfRegistry()
_imitators: Dict[BaseImitator] = dict()

""" init actor handlers """
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

    sgy = spec.get("strategy", "naive")  # default to naive
    imt_build = {
        "naive": NaiveImitator,
        # ..other strategies
    }.get(sgy)
    if imt_build is None:
        return f"invalid strategy {sgy}"

    sn = util.spaced_name(name, namespace)
    imt = imt_build(name=sn)
    imt.spawn(obs_attrs, act_attrs)
    imt.start()
    _imitators[sn] = imt

    return f"start imitator {sn}"


def delete(name, namespace, **kwargs):
    sn = util.spaced_name(name, namespace)
    imt = _imitators.get(sn)
    if imt is not None:
        imt.
    return ""


""" imitators of different strategies """


class BaseImitator:
    def __init__(self, name):
        self.name = name
        self.registry = None
        self.ready_flag = None
        self.stop_flag = None

    def spawn(self, obs_attrs: List[Auri], act_attrs: List[Auri]):
        """Register handler in a new registry."""
        self.registry = KopfRegistry()

        # register handlers
        for au in obs_attrs:
            # TBD auri existence check
            gvr = (au.group, au.version, au.resource)

            @kopf.on.create(*gvr, registry=self.registry)
            def create_fn(name, spec, status, **kwargs):
                print(f"$debug$: create_fn in {name}")
                return {"message": f"update {au.resource}"}

            @kopf.on.update(*gvr, registry=self.registry)
            def update_fn(name, spec, status, **kwargs):
                print(f"$debug$: update_fn in {name}")
                return {"message": f"update {au.resource}"}

            @kopf.on.delete(*gvr, registry=self.registry, optional=True)
            def create_fn(name, spec, status, **kwargs):
                print(f"$debug$: delete_fn in {name}")
                return {"message": f"update {au.resource}"}

        for au in act_attrs:
            gvr = (au.group, au.version, au.resource)

            @kopf.on.create(*gvr, registry=self.registry)
            def create_fn(name, spec, status, **kwargs):
                print(f"$debug$: create_fn in {name}")
                return {"message": f"update {au.resource}"}

            @kopf.on.update(*gvr, registry=self.registry)
            def update_fn(name, spec, status, **kwargs):
                print(f"$debug$: update_fn in {name}")
                return {"message": f"update {au.resource}"}

            @kopf.on.delete(*gvr, registry=self.registry, optional=True)
            def create_fn(name, spec, status, **kwargs):
                print(f"$debug$: delete_fn in {name}")
                return {"message": f"update {au.resource}"}

    def start(self):
        assert self.registry is not None

        self.ready_flag, self.stop_flag = util.run_operator(self.registry)

    def stop(self):
        assert self.stop_flag is not None
        self.stop_flag.set()


class NaiveImitator(BaseImitator):
    def __init__(self, *args, **kwargs):
        # when the imitator starts to report action
        self.thresh = 3
        # obs and actions are stored as tuples
        self.obs_action_freq = defaultdict(lambda: defaultdict(int))
        super().__init__(*args, **kwargs)

    def get_action(self, obs: dict) -> dict:
        action_freq = sorted(self.obs_action_freq[obs].items(),
                             key=lambda x: x[1],
                             reverse=True)
        top_action, freq = action_freq[0]

        if freq > self.thresh:
            return top_action

    def update_obs(self, obs: dict, action: dict):
        self.obs_action_freq[obs][action] += 1


def main():
    print(f"Starting the main operator.")
    _, _ = util.run_operator(_init_registry)
    print("Created main operator thread.")


if __name__ == "__main__":
    main()
