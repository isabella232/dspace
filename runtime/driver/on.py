import os
import util
from reconcile import rc

"""Filters."""


def control(*args, **kwargs):
    # if decorator not parameterized
    if len(args) >= 1 and callable(args[0]):
        return _attr(path="control", *args, **kwargs)

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="control." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="control." + kwargs.pop("path"), *args, **kwargs)

    return decorator


def data(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        return _attr(path="data", *args, **kwargs)

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="data." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="data." + kwargs.pop("path"), *args, **kwargs)

    return decorator


def obs(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        return _attr(path="obs", *args, **kwargs)

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="obs." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="obs." + kwargs.pop("path"), *args, **kwargs)
    return decorator


def mount(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        return _attr(path="mount", *args, **kwargs)

    def decorator(fn):
        if len(args) >= 1:
            _attr(fn, path="mount." + args[0], *args[1:], **kwargs)
        elif "path" in kwargs:
            _attr(fn, path="mount." + kwargs.pop("path"), *args, **kwargs)

    return decorator


# XXX test path
def attr(*args, **kwargs):
    if len(args) >= 1 and callable(args[0]):
        return _attr(path=".", *args, **kwargs)

    def decorator(fn):
        _attr(fn, *args, **kwargs)

    return decorator


def _attr(fn, path=".", priority=0):
    # preprocess the path str -> tuple of str
    _path = list()
    ps = path.split(".")

    if path == ".":
        _path = ["."]
    elif ps[0] == "mount":
        # XXX better . operator handling; use regex
        ps_gvr = path.split("/")
        assert len(ps_gvr) == 1 or len(ps_gvr) == 3
        if len(ps_gvr) == 1:
            # this gvr does not have group and version
            ps[1] = util.gvr(rc.g, rc.v, ps[1])
            _path = ps
        elif len(ps_gvr) == 3:
            gvr = util.gvr(ps_gvr[0].replace("mount.", ""),
                           ps_gvr[1],
                           ps_gvr[2].split(".")[0])
            _path = ["mount", gvr] + ps_gvr[2].split(".")[1:]
    else:
        _path = ps
    # XXX assume default gv in gvr until fix dot in path literal;
    # _path = path.split(".")

    # TBD: join multiple path to allow multiple decorators per handler
    _path = tuple(_path)

    def has_diff(_, diff, *args, **kwargs) -> bool:
        _, _ = args, kwargs
        diff_attrs = {(".",): True}
        for op, fs, old, new in diff:
            diff_attrs.update({
                # Skip "spec" in diff
                fs[1:i + 1]: True
                for i in range(len(fs))
            })
        if _path in diff_attrs or len(diff) == 0:
            return True
        return False

    rc.add(handler=fn,
           priority=priority,
           condition=has_diff,
           path=_path)
