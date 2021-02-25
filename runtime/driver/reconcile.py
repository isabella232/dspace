import os
import typing

from collections import defaultdict


class __Reconciler:
    def __init__(self):
        # handlers are stored as tuples (fn, condition, path, priority)
        # the higher the priority value, the higher the priority;
        # default priority is 0; low priority handlers are run first;
        # priority lower than 0 is skipped.
        # - condition: a function that decides whether the handler
        #   should be run or not.
        # - path: the attribute subtree the handler subscribes to

        # sorted list of handlers in execution order
        self.handlers = list()
        self.g = os.environ["GROUP"]
        self.v = os.environ["VERSION"]
        self.r = os.environ["PLURAL"]

        # list of handlers keyed by the priority;
        # TBD use bisect if no other purpose
        self._prio_handler = defaultdict(list)

    def run(self, spec, *args, **kwargs):
        spec = dict(spec)
        for fn, cond, path, _ in self.handlers:
            if cond(spec, *args, **kwargs):
                sub_spec = safe_lookup(spec, path)
                assert type(sub_spec) is dict
                # handler edits the spec object
                fn(sub_spec)
        return spec

    def add(self, handler: typing.Callable,
            condition: typing.Callable,
            priority: int,
            path: tuple = ()):
        # XXX support reflex API and dynamically add handler
        self._prio_handler[priority].append((handler, condition, path, priority))
        for p in sorted(self._prio_handler.keys()):
            # skip negative priority
            if p < 0:
                continue
            self.handlers += self._prio_handler[p]


def safe_lookup(d: dict, path: tuple):
    for k in path:
        d = d.get(k, {})
    return d


rc = __Reconciler()
