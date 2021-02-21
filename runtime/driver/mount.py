import kopf
import time
import threading
import copy
from collections import defaultdict

import util
from util import parse_gvr, spaced_name, parse_spaced_name

"""
An embedded meta-actor that implements the mount semantics.

Event watch:
- Watch the parent model and identify the child models;
- Watch the child models;

Event propagation:
- On child's updates (intent and status): propagate to the child's 
  copy in the parent;
- On parent's updates (intent) on the child's copy: propagate to 
  the child's intent;
"""


class Watch:
    def __init__(self, g, v, r, n, ns="default", *,
                 create_fn=None,
                 resume_fn=None,
                 update_fn=None,
                 delete_fn=None, delete_optional=False,
                 field_fn=None, field=""):
        self._registry = util.KopfRegistry()
        _args = (g, v, r)
        _kwargs = {
            "registry": self._registry,
            # watch a specific model only
            "when": lambda name, namespace, **_: name == n and namespace == ns,
        }
        if create_fn is not None:
            kopf.on.create(*_args, **_kwargs)(create_fn)
        if resume_fn is not None:
            kopf.on.resume(*_args, **_kwargs)(resume_fn)
        if update_fn is not None:
            kopf.on.update(*_args, **_kwargs)(update_fn)
        if delete_fn is not None:
            kopf.on.delete(*_args, **_kwargs, optional=delete_optional)(delete_fn)
        if field_fn is not None and field != "":
            kopf.on.field(field=field, *_args, **_kwargs)(field_fn)
        assert create_fn or resume_fn or update_fn or delete_fn, "no handler provided"

        self._ready_flag, self._stop_flag = None, None

    def start(self):
        self._ready_flag, self._stop_flag = util.run_operator(self._registry)
        return self

    def stop(self):
        assert self._stop_flag, "watch has not started"
        self._stop_flag.set()
        return self


class Mounter:
    """Implements the mount semantics for a given (parent) digivice"""

    def __init__(self, g, v, r, n, ns="default"):
        # children events handlers
        def _sync_to_parent(spec, diff, *args, **kwargs):
            _, _ = args, kwargs

            # use the diff to filter to only the status/output/obs updates
            # unless the parent does not have the .spec (e.g., at creation)

        def _delete_from_parent(*args, **kwargs):
            _, _ = args, kwargs
            # TBD: get current parent and remove it

        # parent event handlers
        def _update_children_watches(spec: dict):
            # iterate over mounts and add/trim child event watches
            mounts = spec.get("mount", {})

            # add
            for gvr_str, models in mounts.items():
                gvr = parse_gvr(gvr_str)

                for nsn_str, m in models.items():
                    nsn = parse_spaced_name(nsn_str)
                    # in case default ns is omitted in the model
                    nsn_str = spaced_name(*nsn)

                    if gvr_str in self._children_watches and \
                            nsn_str in self._children_watches[gvr_str]:
                        continue

                    # TBD: add child event handlers
                    self._children_watches[gvr_str][nsn_str] \
                        = Watch(*gvr, *nsn, create_fn=lambda *args, **kwargs: 1).start()

            # trim
            for gvr_str, model_watches in self._children_watches.items():
                if gvr_str not in mounts:
                    for _, w in model_watches.items():
                        w.stop()
                    del self._children_watches[gvr_str]

                for nsn_str, w in model_watches.items():
                    models = mounts[gvr_str]
                    if nsn_str not in models and \
                            util.trim_default_space(nsn_str) not in models:
                        w.stop()
                        del model_watches[nsn_str]

        def _sync_to_children(spec, diff):
            # use the diff to filter to only the intent/input updates
            pass

        def on_parent_create(spec, *args, **kwargs):
            _, _ = args, kwargs
            _update_children_watches(spec)

        def on_mount_attr_update(spec, diff, *args, **kwargs):
            _, _ = args, kwargs
            _update_children_watches(spec)
            _sync_to_children(spec, diff)

        def on_parent_delete(*args, **kwargs):
            _, _ = args, kwargs
            self.stop()

        # subscribe to the events of the parent model
        self._parent_watch = Watch(g, v, r, n, ns,
                                   create_fn=on_parent_create,
                                   resume_fn=on_parent_create,
                                   field_fn=on_mount_attr_update, field="spec.mount",
                                   delete_fn=on_parent_delete)

        # subscribe to the events of the child models;
        # keyed by the gvr and then spaced name
        self._children_watches = defaultdict(dict)

    def start(self):
        self._parent_watch.start()

    def stop(self):
        self._parent_watch.stop()
        for _, mws in self._children_watches.items():
            for _, w in mws.items():
                w.stop()
        return self


def test():
    gvr = ("mock.digi.dev", "v1", "samples")
    Mounter(*gvr, n="sample").start()


if __name__ == '__main__':
    test()
