import os
import kopf

import util
from mount import Mounter


def main():
    g = os.environ["GROUP"]
    v = os.environ["VERSION"]
    r = os.environ["PLURAL"]
    n = os.environ["NAME"]
    ns = os.environ.get("NAMESPACE", "default")

    if os.environ.get("MOUNTER", True):
        Mounter(g, v, r, n, ns).start()

    _model = {
        "group": g,
        "version": v,
        "plural": r,
    }
    _registry = util.KopfRegistry()
    _kwargs = {
        "when": lambda name, namespace, **_: name == n and namespace == ns,
        "registry": _registry,
    }
    _ready, _stop = None, None

    import handler  # decorate the handlers
    _ = handler

    from reconcile import rc

    @kopf.on.create(**_model, **_kwargs)
    @kopf.on.resume(**_model, **_kwargs)
    @kopf.on.update(**_model, **_kwargs)
    def reconcile(*args, **kwargs):
        spec = rc.run(*args, **kwargs)
        util.patch_spec(g, v, r, n, ns, spec)

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        _stop.set()

    _ready, _stop = util.run_operator(_registry)


if __name__ == '__main__':
    main()
