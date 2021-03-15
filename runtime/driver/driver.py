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
    def reconcile(meta, *args, **kwargs):
        rv, gn = meta["resourceVersion"], meta["generation"]
        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if rc.gen == gn + 1:
            return

        spec = rc.run(*args, **kwargs)
        e = util.patch_spec(g, v, r, n, ns, spec, rv=rv)
        if e is not None:
            # retry s.t. the diff object contains the past changes
            raise kopf.TemporaryError(e, delay=1)

        rc.gen = gn

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        # use dq to remove the driver
        # _stop.set()

    _ready, _stop = util.run_operator(_registry)


if __name__ == '__main__':
    main()
