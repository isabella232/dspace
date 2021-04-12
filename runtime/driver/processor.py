"""Logic and policy processors"""

import pyjq
import time
from view import ModelView


def jq(policy: str):
    # preproc macro
    _macros = {
        "$time": str(time.time()),
        # ...
    }

    for _m, _v in _macros.items():
        policy = policy.replace(_m, _v)

    def fn(proc_view, *args, **kwargs):
        _, _ = args, kwargs
        with ModelView(proc_view) as mv:
            mv.update(pyjq.one(policy, mv))

    return fn


def py(policy: str):
    return NotImplemented