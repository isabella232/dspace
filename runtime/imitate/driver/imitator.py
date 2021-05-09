import abc
from typing import List
from collections import defaultdict

import kopf
import util
from util import Auri, Attr, KopfRegistry

""" imitators of different strategies """


def get_builder(strategy: str):
    return {
        "naive": NaiveImitator,
        # ..other strategies
    }.get(strategy)


class Imitator:
    __metaclass__ = abc.ABCMeta

    def __init__(self, name):
        self.name = name
        self._registry = None
        self._ready_flag = None
        self._stop_flag = None

        # TBD feature representation
        # the states are represented as k-v pairs where each key
        # is an auri; values are exported in lexica
        # self.obs = XXX
        # self.action = XXX

    @abc.abstractmethod
    def update_obs_action(self, obs, action):
        """"""

    @abc.abstractmethod
    def gen_action(self, obs):
        """"""

    @abc.abstractmethod
    def do(self, action):
        """"""

    def spawn(self, obs_attrs: List[Auri], act_attrs: List[Auri]):
        """Define and register handlers in a new registry."""
        self._registry = KopfRegistry()

        # register handlers
        for au in obs_attrs:
            # TBD auri existence check
            _gvr = (au.group, au.version, au.resource)
            _kwargs = {
                "registry": self._registry,
                "when": name_matcher(au.name, au.namespace),
            }

            @kopf.on.create(*_gvr, **_kwargs)
            def create_fn(name, spec, status, **kwargs):
                # TBD: how to model the obs_action tuple
                # self.update_obs_action()

                print(f"$debug$: obs create_fn in {name}")

            @kopf.on.update(*_gvr, **_kwargs)
            def update_fn(name, spec, status, **kwargs):
                print(f"$debug$: obs update_fn in {name}")

            @kopf.on.delete(*_gvr, **_kwargs, optional=True)
            def delete_fn(name, spec, status, **kwargs):
                print(f"$debug$: obs delete_fn in {name}")

        for au in act_attrs:
            gvr = (au.group, au.version, au.resource)

            @kopf.on.create(*gvr, registry=self._registry)
            def create_fn(name, spec, status, **kwargs):
                print(f"$debug$: action create_fn in {name}")

            @kopf.on.update(*gvr, registry=self._registry)
            def update_fn(name, spec, status, **kwargs):
                print(f"$debug$: action update_fn in {name}")

            @kopf.on.delete(*gvr, registry=self._registry, optional=True)
            def delete_fn(name, spec, status, **kwargs):
                print(f"$debug$: action delete_fn in {name}")

    def start(self):
        assert self._registry is not None

        self._ready_flag, self._stop_flag = util.run_operator(self._registry)

    def stop(self):
        assert self._stop_flag is not None
        self._stop_flag.set()


class NaiveImitator(Imitator):
    def __init__(self, *args, **kwargs):
        # when the imitator starts to report action
        self.thresh = 3
        # obs and actions are stored as tuples
        self.obs_action_freq = defaultdict(lambda: defaultdict(int))
        super().__init__(*args, **kwargs)

    def update_obs_action(self, obs, action):
        self.obs_action_freq[obs][action] += 1

    def gen_action(self, obs) -> dict:
        action_freq = sorted(self.obs_action_freq[obs].items(),
                             key=lambda x: x[1],
                             reverse=True)
        top_action, freq = action_freq[0]

        if freq > self.thresh:
            return top_action

    def do(self, action):
        pass


def name_matcher(n, ns):
    def f(name, namespace, **_):
        # print("$debug:$ matcher", name, namespace)
        return name == n and namespace == ns
    return f
