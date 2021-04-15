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
    th

    - TBD: add mounts recursively but trim off each's mounts
    - TBD: add trim hint to reduce the size of view
    - TBD: support source views besides root
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
        # apply
        _root = self._root_view
        _diffs = diff(self._old, self._new)
        # print("debug:", _diffs)
        for op, path, old, new in _diffs:
            nsn = path[0]
            if nsn == "root":
                deep_set(_root, ".".join(path[1:]), new)
            else:
                typ = self._nsn_gvr[nsn]
                nsn = util.normalized_nsn(nsn)
                path = f"mount.{typ}.{nsn}" + ".".join(path[1])
                deep_set(_root, path, new)


class TypeView:
    """
    Return models group-by their gvr, if the gv is
    the same as the parent's gv, it will be trimmed
    to only the plural.

    - TBDs: ditto
    """

    def __init__(self, root_view: dict, gv_str: str):
        self._root_view = root_view
        self._old, self._new = None, None
        self._gv_str = gv_str

    def __enter__(self):
        _view = {"root": self._root_view}
        _mount = self._root_view.get("mount", {})

        for typ, ms in _mount.items():
            _typ_n = typ.replace(self._gv_str, "")
            _view[_typ_n] = {}
            for n, m in ms.items():

                m = m.get("spec", {})
                n = n.replace("default/", "")
                if len(m) > 0:
                    _view[_typ_n].update({n: m})

        self._old, self._new = _view, copy.deepcopy(_view)
        return self._new

    def __exit__(self, typ, value, traceback):
        # TBD
        raise NotImplementedError


class DotView:
    # TBD
    def __init__(self):
        raise NotImplementedError


def test():
    import yaml
    import pprint as pp
    test_yaml = """
    control:
      brightness:
        intent: 0.8
        status: 0
      mode:
        intent: sleep
        status: sleep
    mount:
      mock.digi.dev/v1/lamps:
        default/lamp-test:
          spec:
            control:
              power: 
                intent: "on"
    """
    v = yaml.load(test_yaml, Loader=yaml.FullLoader)
    print("before:", v)
    with ModelView(v) as mv:
        pp.pprint(mv)
        mv["root"]["control"]["mode"]["intent"] = "work"
        print("-----")
    print("after:", v)


if __name__ == '__main__':
    test()
