import asyncio
import contextlib
import threading
import inflection

import kubernetes
from kubernetes.client.rest import ApiException
import kopf
from kopf.reactor.registries import SmartOperatorRegistry as KopfRegistry

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


def update_status(gvr: dict, status):
    api = kubernetes.client.CustomObjectsApi()

    try:
        api.patch_namespaced_custom_object_status(group=gvr["group"],
                                                  version=gvr["version"],
                                                  namespace=gvr.get("namespace", "default"),
                                                  name=gvr["name"],
                                                  plural=gvr["plural"],
                                                  body={
                                                      "status": status,
                                                  },
                                                  )
    except ApiException as e:
        print(f"k8s: unable to update resource {gvr}:", e)


if __name__ == "__main__":
    import pprint as pp
    # kubernetes.config.load_incluster_config()
    test_spec = {'apiVersion': 'digi.dev/v1', 'kind': 'Imitate', 'metadata': {'annotations': {
        'kubectl.kubernetes.io/last-applied-configuration': '{"apiVersion":"digi.dev/v1","kind":"Imitate","metadata":{"annotations":{},"name":"mock-imitate","namespace":"default"},"spec":{"action":["/MockLamp/mock-lamp-2.spec.power"],"obs":["/MockLamp/mock-lamp-1.power"],"strategy":"naive"}}\n'},
        'creationTimestamp': '2020-12-30T17:48:38Z',
        'finalizers': [
            'kopf.zalando.org/KopfFinalizerMarker'],
        'generation': 1, 'managedFields': [
            {'apiVersion': 'digi.dev/v1', 'fieldsType': 'FieldsV1',
             'fieldsV1': {'f:metadata': {'f:finalizers': {'.': {}, 'v:"kopf.zalando.org/KopfFinalizerMarker"': {}}}},
             'manager': 'kopf', 'operation': 'Update', 'time': '2020-12-30T17:48:38Z'},
            {'apiVersion': 'digi.dev/v1', 'fieldsType': 'FieldsV1', 'fieldsV1': {
                'f:metadata': {'f:annotations': {'.': {}, 'f:kubectl.kubernetes.io/last-applied-configuration': {}}},
                'f:spec': {'.': {}, 'f:action': {}, 'f:obs': {}, 'f:strategy': {}}}, 'manager': 'kubectl',
             'operation': 'Update', 'time': '2020-12-30T17:48:38Z'}], 'name': 'mock-imitate', 'namespace': 'default',
        'resourceVersion': '2371250',
        'selfLink': '/apis/digi.dev/v1/namespaces/default/imitates/mock-imitate',
        'uid': '55ec564f-1854-4364-bc23-082b5738a70c'},
                 'spec': {'action': ['/MockLamp/mock-lamp-2.spec.power'], 'obs': ['/MockLamp/mock-lamp-1.power'],
                          'strategy': 'naive'}}

    pp.pprint(parse_auri("/MockLamp/mock-lamp-2.spec.power"))
    pp.pprint(parse_attr(test_spec, ".obs"))
    pp.pprint(parse_attr(test_spec, ".spec.obs"))
