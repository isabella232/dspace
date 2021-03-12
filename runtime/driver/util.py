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

try:
    # deployed with service config
    config.load_incluster_config()
except:
    # deployed with kubeconfig
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


def spaced_name(n, ns) -> str:
    return f"{ns}/{n}"


def trim_default_space(s):
    return s.lstrip("default/")


def gvr_from_body(b):
    g, v = tuple(b["apiVersion"].split("/"))
    r = inflection.pluralize(b["kind"].lower())
    return g, v, r


def parse_spaced_name(nsn) -> Tuple[str, str]:
    parsed = nsn.split("/")
    if len(parsed) < 2:
        return parsed[0], "default"
    # name, namespace
    return parsed[1], parsed[0]


def parse_gvr(gvr: str, g="", v="") -> Tuple[str, ...]:
    parsed = tuple(gvr.lstrip("/").split("/"))
    assert len(parsed) == 3, f"{gvr} not in form of '[/]group/version/plural'"
    # if len(parsed) != 3:
    #     assert g != "" and v != "", "provide group and version to complete the gvr"
    #     return g, v, parsed[-1]
    return parsed


def model_id(g, v, r, n, ns) -> str:
    return f"{g}/{v}/{r}/{spaced_name(n, ns)}"


def gvr(g, v, r) -> str:
    return f"{g}/{v}/{r}"


def is_gvr(s: str) -> bool:
    return len(s.split("/")) == 3


def normalized_gvr(s, g, v) -> str:
    r = s.split("/")[-1]
    return f"{g}/{v}/{r}"


def safe_attr(s):
    return s.replace(".", "-")


def parse_model_id(s) -> Tuple[str, str, str, str, str]:
    ps = s.lstrip("/").split("/")
    assert len(ps) in {4, 5}
    if len(ps) == 4:
        return ps[0], ps[1], ps[2], ps[3], "default"
    return ps[0], ps[1], ps[2], ps[4], ps[3]


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


# TBD: honor resource version
# def get_model():
#     pass

# def update_model():
#     pass


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
