"""Views used for manipulation."""
import os
import copy
from box import Box
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


class TypeView:
    """
    Return models group-by their gvr, if the gv is
    the same as the parent's gv, it will be trimmed
    to only the plural.

    TBDs: ditto
    """

    def __init__(self, root_view: dict, gvr_str: str = None):
        self._root_view = root_view
        self._old, self._new = None, None

        if gvr_str is None:
            assert "GROUP" in os.environ and \
                   "VERSION" in os.environ and \
                   "PLURAL" in os.environ
            self._r = os.environ["PLURAL"]
            self._gv_str = f"{os.environ['GROUP']}" \
                           f"/{os.environ['VERSION']}"
            self._gvr_str = f"{self._gv_str}/{os.environ['PLURAL']}"
        else:
            gvr_str = util.full_gvr(gvr_str)
            self._r = util.parse_gvr(gvr_str)[-1]
            self._gv_str = "/".join(util.parse_gvr(gvr_str)[:-1])
            self._gvr_str = gvr_str

        self._typ_full_typ = dict()

    def __enter__(self):
        _view = {self._r: {"root": self._root_view}}
        _mount = self._root_view.get("mount", {})

        for typ, ms in _mount.items():
            _typ = typ.replace(self._gv_str + "/", "")
            _view[_typ] = {}
            self._typ_full_typ[_typ] = typ

            for n, m in ms.items():
                if "spec" not in m:
                    m = m.get("spec", {})
                n = n.replace("default/", "")
                _view[_typ].update({n: m["spec"]})

        self._old, self._new = _view, copy.deepcopy(_view)
        return self._new

    def __exit__(self, typ, value, traceback):
        _root = self._root_view
        _diffs = diff(self._old, self._new)

        for op, path, old, new in _diffs:
            typ = path[0]
            if typ == self._r:
                deep_set(_root, ".".join(path[2:]), new)
            else:
                typ = self._typ_full_typ[typ]
                nsn = util.normalized_nsn(path[1])
                path = ["mount", typ, nsn, "spec"] + list(path[2:])
                deep_set(_root, path, new)
