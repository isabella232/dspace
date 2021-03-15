import kubernetes
from kubernetes.client.rest import ApiException
from kubernetes import client, config
from kubernetes.client.rest import ApiException

try:
    # deployed with service config
    config.load_incluster_config()
except:
    # deployed with kubeconfig
    config.load_kube_config()


def spaced_name(n, ns) -> str:
    return f"{ns}/{n}"


def model_id(g, v, r, n, ns) -> str:
    return f"{g}/{v}/{r}/{spaced_name(n, ns)}"


import util

# s, rv, gen = util.get_spec("mock.digi.dev", "v1", "lamps", "lamp-test", "default")
# print(s, rv)
# t = util.patch_spec("mock.digi.dev", "v1", "lamps", "lamp-test", "default", s["spec"], rv="3530644")
import kopf


@kopf.on.create("mock.digi.dev", "v1", "lamps")
# @kopf.on.update("mock.digi.dev", "v1", "lamps")
def h1(spec, diff, meta, *args, **kwargs):
    print(meta["resourceVersion"])
    print(diff)
    # print(spec)
    # raise kopf.TemporaryError("asdf", delay=1)
