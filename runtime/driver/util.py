import asyncio
import contextlib
import threading
import inflection
from typing import Tuple

import kubernetes
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.client.rest import ApiException

import kopf
from kopf.reactor.registries import SmartOperatorRegistry as KopfRegistry

config.load_kube_config()

KopfRegistry = KopfRegistry


def run_operator(registry: KopfRegistry, verbose=True) -> (threading.Event, threading.Event):
    ready_flag = threading.Event()
    stop_flag = threading.Event()

    def kopf_thread():
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        with contextlib.closing(loop):
            kopf.configure(verbose=verbose)
            loop.run_until_complete(kopf.operator(
                ready_flag=ready_flag,
                stop_flag=stop_flag,
                registry=registry,
            ))

    thread = threading.Thread(target=kopf_thread)
    thread.start()
    print(f"Started new operator.")
    return ready_flag, stop_flag


class NamespacedName:
    def __init__(self, n, ns="default"):
        self.name = n
        self.namespace = ns


class Auri:
    def __init__(self, **kwargs):
        self.group = str(kwargs["group"])
        self.version = str(kwargs["version"])
        self.kind = str(kwargs["kind"]).lower()
        self.resource = inflection.pluralize(self.kind)
        self.name = str(kwargs["name"])
        self.namespace = str(kwargs["namespace"])
        self.path = str(kwargs["path"])

    def gvr(self) -> tuple:
        return self.group, self.version, self.resource

    def gvk(self) -> tuple:
        return self.group, self.version, self.kind

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return f"" \
               f"/{self.group}" \
               f"/{self.version}" \
               f"/{self.kind}" \
               f"/{self.namespace}" \
               f"/{self.name}{self.path}"


def parse_auri(s: str) -> Auri or None:
    ps = s.partition(".")
    main_segs = ps[0].lstrip("/").split("/")
    attr_path = "" if len(ps) < 2 else "." + ps[2]

    parsed = {
        2: lambda x: {
            "group": "digi.dev",
            "version": "v1",
            "kind": x[0],
            "name": x[1],
            "namespace": "default",
            "path": attr_path,
        },
        3: lambda x: {
            "group": "digi.dev",
            "version": "v1",
            "kind": x[0],
            "name": x[2],
            "namespace": x[1],
            "path": attr_path,
        },
        5: lambda x: {
            "group": x[0],
            "version": x[1],
            "kind": x[2],
            "name": x[3],
            "namespace": x[4],
            "path": attr_path,
        },
    }.get(len(main_segs), lambda: {})(main_segs)

    if parsed is None:
        return None
    return Auri(**parsed)


class Attr:
    def __init__(self):
        pass

    def flattened(self):
        pass


def parse_attr(obj, path: str):
    # TBD
    pass


def spaced_name(n, ns):
    return f"{ns}/{n}"


def trim_default_space(s):
    return s.lstrip("default/")


def attr_updated(diff: Tuple, path: str):
    for _, f, _, _ in diff:
        if f[:len(path)] == tuple(path.lstrip("/").split("/")):
            return True
    return False


def parse_spaced_name(nsn):
    parsed = nsn.split("/")
    if len(parsed) < 2:
        return parsed[0], "default"
    # name, namespace
    return parsed[1], parsed[0]


def parse_gvr(gvr: str) -> Tuple[str, ...]:
    parsed = tuple(gvr.split("/"))
    assert len(parsed) == 3, f"unrecognized {gvr}, should be in form of '/group/version/plural'"
    return parsed


def model_id(g, v, r, n, ns):
    return f"{g}/{v}/{r}/{spaced_name(n, ns)}"


def get_spec(g, v, r, n, ns):
    api = kubernetes.client.CustomObjectsApi()

    try:
        o = api.get_namespaced_custom_object(group=g,
                                             version=v,
                                             namespace=ns,
                                             name=n,
                                             plural=r,
                                             )
    except ApiException as e:
        print(f"k8s: unable to update model {model_id(g, v, r, n, ns)}:", e)
        return None
    return o.get("spec", {})


def patch_spec(g, v, r, n, ns, spec: dict):
    api = kubernetes.client.CustomObjectsApi()

    try:
        api.patch_namespaced_custom_object(group=g,
                                           version=v,
                                           namespace=ns,
                                           name=n,
                                           plural=r,
                                           body={
                                               "spec": spec,
                                           },
                                           )
    except ApiException as e:
        print(f"k8s: unable to update model {model_id(g, v, r, n, ns)}:", e)


if __name__ == "__main__":
    import pprint as pp

    pp.pprint(parse_auri("/MockLamp/mock-lamp-2.spec.power"))
