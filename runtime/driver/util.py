import os
import asyncio
import contextlib
import threading
import inflection
from typing import Tuple, Callable
from functools import reduce

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

GEN_OUTDATED = 41


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


def trim_attr(spec: dict, attrs: set) -> dict:
    # BFS
    to_visit = [spec]
    for n in to_visit:
        to_trim = list()
        if type(n) is not dict:
            continue
        for k, v in n.items():
            if k not in attrs:
                to_visit.append(v)
            else:
                to_trim.append(k)
        for k in to_trim:
            n.pop(k, {})
    return spec


def apply_diff(model: dict, diff: list) -> dict:
    for op, fs, old, new in diff:
        if len(fs) == 0:
            continue
        if op in {"add", "change"}:
            n = model
            for f in fs[:-1]:
                if f not in n:
                    n[f] = dict()
                n = n[f]
            n[fs[-1]] = new
    return model


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


def get_spec(g, v, r, n, ns) -> (dict, str, int):
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
    return o.get("spec", {}), \
           o["metadata"]["resourceVersion"], \
           o["metadata"]["generation"]


def patch_spec(g, v, r, n, ns, spec: dict, rv=None):
    api = kubernetes.client.CustomObjectsApi()

    try:
        resp = api.patch_namespaced_custom_object(group=g,
                                                  version=v,
                                                  namespace=ns,
                                                  name=n,
                                                  plural=r,
                                                  body={
                                                      "metadata": {} if rv is None else {
                                                          "resourceVersion": rv,
                                                      },
                                                      "spec": spec,
                                                  },
                                                  )
        return resp, None
    except ApiException as e:
        return None, e


def check_gen_and_patch_spec(g, v, r, n, ns, spec, gen):
    # patch the spec atomically if the current gen is
    # less than the given spec
    while True:
        _, rv, cur_gen = get_spec(g, v, r, n, ns)
        if gen < cur_gen:
            e = ApiException()
            e.status = GEN_OUTDATED
            return cur_gen, None, e

        resp, e = patch_spec(g, v, r, n, ns, spec, rv=rv)
        if e is None:
            return cur_gen, resp, None
        if e.status == 409:
            print(f"unable to patch model due to conflict; retry")
        else:
            print(f"patch error {e}")
            return cur_gen, resp, e


# utils
def put(path, src, target, transform=lambda x: x):
    if not isinstance(target, dict):
        return

    ps = path.split(".")
    for p in ps[:-1]:
        if p not in target:
            return
        target = target[p]

    if not isinstance(src, dict):
        if src is None:
            target[ps[-1]] = None
        else:
            target[ps[-1]] = transform(src)
        return

    for p in ps[:-1]:
        if p not in src:
            return
        src = src[p]
    target[ps[-1]] = transform(src[ps[-1]])


def deep_get(d: dict, path: str, default=None):
    return reduce(lambda _d, key: _d.get(key, default) if isinstance(_d, dict) else default, path.split("."),
                  d)


def deep_set(d: dict, path: str, val):
    keys = path.split(".")
    for k in keys[:-1]:
        if k not in d:
            return
        d = d[k]
    d[keys[-1]] = val


def first_attr(attr, d: dict):
    if type(d) is not dict:
        return None
    if attr in d:
        return d[attr]
    for k, v in d.items():
        v = first_attr(attr, v)
        if v is not None:
            return v
    return None


def first_type(mounts):
    if type(mounts) is not dict or len(mounts) == 0:
        return None
    return list(mounts.keys())[0]


def full_gvr(a: str) -> str:
    # full gvr: group/version/plural
    if len(a.split("/")) == 1:
        return "/".join([os.environ["GROUP"],
                         os.environ["VERSION"],
                         a])
    else:
        return a


def gvr_equal(a: str, b: str) -> bool:
    return full_gvr(a) == full_gvr(b)


if __name__ == "__main__":
    import json

    print(parse_auri("/MockLamp/mock-lamp-2.spec.power"))

    A = {"control": {"power": {"intent": "off", "status": "on",
                               "room": {"mode": {"intent": "on",
                                                 "status": "off"}}}},
         "data": {"input": {"url": "http://"}, "output": {"objects": "human"}}}
    print("before:")


    def pprint(s):
        print(json.dumps(A, indent=2))


    pprint(A)
    for t in ["intent", "status", "output"]:
        print(f"after trimming {t}")
        pprint(trim_attr(A, {t}))

    diff = [('add', ('spec', 'labels', 'label1'), None, 'new-value'),
            ('change', ('spec', 'size'), '1G', '2G')]
    A = {"spec": {"size": "1G"}}
    print("after applying diff")
    pprint(apply_diff(A, diff))
