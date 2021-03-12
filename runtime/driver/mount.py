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
                 # TBD enable finalizer but avoid looping with multiple children
                 delete_fn=None, delete_optional=True,
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
        def on_child_create(body, *args, **kwargs):
            _, _ = args, kwargs
            return _sync_to_parent(*util.gvr_from_body(body), **kwargs)

        def on_child_update(body, *args, **kwargs):
            _, _ = args, kwargs
            return _sync_to_parent(*util.gvr_from_body(body), **kwargs)

        def on_child_delete(body, name, namespace,
                            *args, **kwargs):
            _, _ = args, kwargs

            group, version, plural = util.gvr_from_body(body)

            # remove watch
            gvr_str = util.gvr(group, version, plural)
            nsn_str = util.spaced_name(name, namespace)

            w = self._children_watches.get(gvr_str, {}).get(nsn_str, None)
            if w is not None:
                w.stop()
                self._children_watches[gvr_str].pop(nsn_str, "")

            parent = util.get_spec(g, v, r, n, ns)

            # delete from parent
            ps = _gen_parent_spec(parent, None, group, version, plural,
                                  name, namespace)
            if ps is None:
                return
            util.patch_spec(g, v, r, n, ns, ps)

        def _sync_to_parent(group, version, plural, name, namespace,
                            spec, diff, *args, **kwargs):
            _, _ = args, kwargs

            parent = util.get_spec(g, v, r, n, ns)

            parent_spec = _gen_parent_spec(parent, spec,
                                           group, version, plural,
                                           name, namespace)
            if parent_spec is None:
                return

            # use the diff to filter to only the status/output/obs updates
            # unless the parent does not have the .spec (e.g., at creation);
            # filter to only the status/output updates
            for _, f, _, new in diff:
                if len(f) > 0 and f[0] == "spec":
                    fs = set(f)
                    # XXX fix the false positives
                    if (("control" in fs and "intent" in fs) or
                            ("data" in fs and "input" in fs)):
                        # XXX allow intent back-propagation
                        print(f"updates to parent should not contain changes to"
                              f"intent or input attributes, skip {namespace}/{name} "
                              f"for {ns}/{ns}")
                        return

            # push to parent models
            util.patch_spec(g, v, r, n, ns, parent_spec)

        def _gen_parent_spec(parent, child_spec, g_, v_, r_, n_, ns_):
            mounts = parent.get("mount", {})
            gvr_str = util.gvr(g_, v_, r_)
            nsn_str = util.spaced_name(n_, ns_)
            child_spec = dict(child_spec)

            if (gvr_str not in mounts or
                    (nsn_str not in mounts[gvr_str] and
                     n_ not in mounts[gvr_str])):
                print(f"unable to find the {nsn_str} or {n_} in the {parent}")
                return None

            models = mounts[gvr_str]
            n_ = n_ if n_ in models else nsn_str

            if child_spec is None:
                models.pop(n_, {})
                return parent

            # XXX remove when admission controller in
            if type(models[n_]) != dict:
                models[n_] = dict()

            models[n_]["spec"] = child_spec

            if models[n_].get("mode", "hide"):
                models[n_]["spec"].pop("mount", {})

            return parent

        # parent event handlers
        def on_parent_create(spec, diff, *args, **kwargs):
            _, _ = args, kwargs
            _update_children_watches(spec)

        def on_mount_attr_update(spec, diff, *args, **kwargs):
            _, _ = args, kwargs
            _update_children_watches(spec)
            _sync_to_children(spec, diff)

        def on_parent_delete(*args, **kwargs):
            _, _ = args, kwargs
            self.stop()

        def _update_children_watches(spec: dict):
            # iterate over mounts and add/trim child event watches
            mounts = spec.get("mount", {})

            # add watches
            for gvr_str, models in mounts.items():
                # TBD child's gvr, which can omit the group and version
                # for which we use the parent's g and v instead
                # gvr = parse_gvr(gvr_str, g=g, v=v)

                gvr = parse_gvr(gvr_str)  # child's gvr

                for nsn_str, m in models.items():
                    nsn = parse_spaced_name(nsn_str)
                    # in case default ns is omitted in the model
                    nsn_str = spaced_name(*nsn)

                    if gvr_str in self._children_watches and \
                            nsn_str in self._children_watches[gvr_str]:
                        continue

                    # TBD: add child event handlers
                    self._children_watches[gvr_str][nsn_str] \
                        = Watch(*gvr, *nsn,
                                create_fn=on_child_create,
                                resume_fn=on_child_create,
                                update_fn=on_child_update,
                                delete_fn=on_child_delete).start()

            # trim watches no longer needed
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

        def _gen_child_spec(parent_spec, gvr_str, nsn_str):
            mount_entry = parent_spec \
                .get("mount", {}) \
                .get(gvr_str, {}) \
                .get(nsn_str, {})
            if mount_entry.get("mode", "hide") == "hide":
                mount_entry.get("spec", {}).pop("mount", {})
            if mount_entry.get("status", "inactive") == "active":
                return mount_entry.get("spec", None)
            return None

        def _sync_to_children(parent_spec, diff):
            # sort the diff by the attribute path (in tuple)
            diff = sorted(diff, key=lambda x: x[1])

            # filter to only the intent/input updates
            to_sync, to_filter = dict(), dict()
            for _, f, _, _ in diff:
                if len(f) >= 3:
                    gvr_str, nsn_str = f[0], f[1]
                    model_id = util.model_id(*parse_gvr(gvr_str),
                                             *parse_spaced_name(nsn_str))

                    fs = set(f)
                    # XXX fix the false negatives (and false positives for the
                    # to-filter), or reserve e.g. intent as key word;
                    if (model_id not in to_sync and
                            (f[2] in {"mode", "status"} or
                             ("control" in fs and "intent" in fs) or
                             ("data" in fs and "input" in fs))):
                        cs = _gen_child_spec(parent_spec, gvr_str, nsn_str)
                        if cs is not None:
                            to_sync[model_id] = cs

                    if (f[1] == "obs" or ("control" in fs and "status" in fs)
                            or ("data" in fs and "output" in fs)):
                        print(f"children updates should not contain status "
                              f"or output attribute, skip {model_id}")
                        to_filter[model_id] = True

            for k, _ in to_filter.items():
                to_sync.pop(k, "")

            # push to children models
            for model_id, child_spec in to_sync.items():
                util.patch_spec(*util.parse_model_id(model_id), child_spec)

        # subscribe to the events of the parent model
        self._parent_watch = Watch(g, v, r, n, ns,
                                   create_fn=on_parent_create,
                                   resume_fn=on_parent_create,
                                   field_fn=on_mount_attr_update, field="spec.mount",
                                   delete_fn=on_parent_delete, delete_optional=True)

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
