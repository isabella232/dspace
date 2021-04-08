import os
import sys
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
        self.skip_gen = -1

        # list of handlers keyed by the priority;
        # TBD use bisect if no other purpose
        self._prio_handler = defaultdict(list)

    def run(self, spec, old, diff, *args, **kwargs):
        spec = dict(spec)
        proc_spec = dict(spec)
        for fn, cond, path, _ in self.handlers:
            if cond(proc_spec, diff, *args, **kwargs):
                sub_spec = safe_lookup(proc_spec, path)
                # handler edits the spec object
                try:
                    fn(subview=sub_spec, proc_view=proc_spec,
                       view=spec, old_view=old,
                       mount=proc_spec.get("mount", {}),
                       back_prop=get_back_prop(diff), diff=diff)
                except Exception as e:
                    print(f"reconcile error: {e.with_traceback(sys.exc_info()[2])}")
                    return proc_spec
                # TBD: detect changes and add to diff
                # TBD: reason/debug operator
        return proc_spec

    def add(self, handler: typing.Callable,
            condition: typing.Callable,
            priority: int,
            path: tuple = ()):

        # XXX support reflex API and dynamically add handler
        # XXX each handler should be registered only once but allow chained conditions
        self._prio_handler[priority].append((handler, condition, path, priority))
        for p in sorted(self._prio_handler.keys()):
            # skip negative priority
            if p < 0:
                continue
            self.handlers += self._prio_handler[p]


def safe_lookup(d: dict, path: tuple):
    if path == (".",):
        return d

    for k in path:
        d = d.get(k, {})
    return d


def get_back_prop(diff):
    bp = list()
    for op, path, old, new in diff:
        if op != "change" and op != "add":
            continue
        if len(path) < 3 or path[0] != "spec" \
                or path[1] != "mount":
            continue

        fs = set(path)
        if "intent" not in fs and "input" not in fs:
            continue
        bp.append((op, path, old, new))
    return bp


rc = __Reconciler()
