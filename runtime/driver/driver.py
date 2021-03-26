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

    if os.environ.get("MOUNTER", "true") != "false":
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

    @kopf.on.startup(registry=_registry)
    def configure(settings: kopf.OperatorSettings, **_):
        settings.persistence.progress_storage = kopf.AnnotationsProgressStorage()

    from reconcile import rc

    @kopf.on.create(**_model, **_kwargs)
    @kopf.on.resume(**_model, **_kwargs)
    @kopf.on.update(**_model, **_kwargs)
    def reconcile(meta, *args, **kwargs):
        gen = meta["generation"]
        # skip the last self-write
        # TBD for parallel reconciliation may need to lock rc.gen before patch
        if gen == rc.gen:
            return

        spec = rc.run(*args, **kwargs)
        e = util.check_gen_and_patch_spec(g, v, r, n, ns, spec, gen=gen)
        if e is not None:
            # retry s.t. the diff object contains the past changes
            raise kopf.TemporaryError(e, delay=0)  # TBD(@kopf) non-zero delay fix
        rc.gen = gen + 1

    @kopf.on.delete(**_model, **_kwargs, optional=True)
    def on_delete(*args, **kwargs):
        _, _ = args, kwargs
        # use dq to remove the driver
        # _stop.set()

    _ready, _stop = util.run_operator(_registry)


if __name__ == '__main__':
    main()
