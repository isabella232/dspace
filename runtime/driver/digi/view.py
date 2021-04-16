"""Views used for manipulation."""
import copy
from kopf.structs.diffs import diff

import digi.util as util
from digi.util import deep_set


class ModelView:
    """
    Return all models in the current world/root view
    keyed by the namespaced name; if the nsn starts
    with default, it will be trimmed off; the original
    view is keyed by "root". Empty model without "spec"
    will be skipped.

    The __enter__ method constructs the model view from
    the root_view and __exit__ applies the changes back
    to the root_view.

    TBD: add mounts recursively but trim off each's mounts
    TBD: add trim hint to reduce the size of view
    TBD: support source views besides root
    """

    def __init__(self, root_view: dict):
        self._root_view = root_view
        self._old, self._new = None, None

        self._nsn_gvr = dict()

    def __enter__(self):
        _view = {"root": self._root_view}
        _mount = self._root_view.get("mount", {})

        for typ, ms in _mount.items():

            for n, m in ms.items():
                if "spec" not in m:
                    continue
                n = n.replace("default/", "")
                _view.update({n: m["spec"]})
                self._nsn_gvr[n] = typ

        self._old, self._new = _view, copy.deepcopy(_view)
        return self._new

    def __exit__(self, typ, value, traceback):
        # diff and apply
        _root = self._root_view
        _diffs = diff(self._old, self._new)
        for op, path, old, new in _diffs:
            nsn = path[0]
            if nsn == "root":
                deep_set(_root, ".".join(path[1:]), new)
            else:
                typ = self._nsn_gvr[nsn]
                nsn = util.normalized_nsn(nsn)
                path = ["mount", typ, nsn, "spec"] + list(path[1:])
                deep_set(_root, path, new)
