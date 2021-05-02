import random
import time
import kopf

import logging
import kubernetes
from digi.util import patch_spec, get_spec, KopfRegistry, run_operator

room = ("bench.digi.dev", "v1", "rooms", "room-test", "default")


@kopf.on.create(*room[:3])
@kopf.on.resume(*room[:3])
@kopf.on.update(*room[:3])
def h(*args, **kwargs):
    print("###time:", time.time())
    send_request(room, {
        "control": {
            "brightness": {
                "intent": random.randint(1, 100000000)
            }
        }
    })


def send_request(auri, s: dict):
    resp, e = patch_spec(*auri, s)
    if e is not None:
        print(f"bench: encountered error {e} \n {resp}")
        exit()


def bench_kopf():
    _registry = KopfRegistry()
    _kwargs = {
        "registry": _registry,
    }

    @kopf.on.login(retries=3, **_kwargs)
    def login_fn(**kwargs):
        import dataclasses
        c = kopf.login_via_client(**kwargs)
        c = dataclasses.replace(c, insecure=True)
        return c

    @kopf.on.update(*room[:3], **_kwargs)
    def h_room(*args, **kwargs):
        # logging.error(f"update: {time.time() - start}")
        print(f"update: {time.time() - start}")

    # run_operator(_registry, log_level=logging.DEBUG)
    run_operator(_registry, log_level=logging.INFO)

    time.sleep(2)
    start = time.time()

    api = kubernetes.client.CustomObjectsApi()

    def send():
        resp = api.patch_namespaced_custom_object(group="bench.digi.dev",
                                                  version="v1",
                                                  namespace="default",
                                                  name="room-test",
                                                  plural="rooms",
                                                  body={
                                                      "spec": {
                                                          "control": {
                                                              "brightness": {"intent": random.randint(1, 10000)}},
                                                      },
                                                  },
                                                  )

    send()

    time.sleep(2)
    start = time.time()
    send()

    time.sleep(2)
    start = time.time()
    send()

    time.sleep(3600)


def bench_k8s():
    api = kubernetes.client.CustomObjectsApi()
    coreapi = kubernetes.client.CoreV1Api()
    try:
        start = time.time()
        coreapi.patch_namespaced_pod(
            namespace="default",
            name="room-test-96b78c8bf-nvrct",
            body={
                "spec": {},
            },
        )
        print("pod", time.time() - start)

        start = time.time()
        _ = api.patch_namespaced_custom_object(group="bench.digi.dev",
                                               version="v1",
                                               namespace="default",
                                               name="room-test",
                                               plural="rooms",
                                               body={
                                                   "spec": {},
                                               },
                                               )
        print("room", time.time() - start)

        start = time.time()
        _ = api.patch_namespaced_custom_object(group="bench.digi.dev",
                                               version="v1",
                                               namespace="default",
                                               name="room-test",
                                               plural="rooms",
                                               body={
                                                   "spec": {},
                                               },
                                               )
        print("room", time.time() - start)

        # TBD benchmark get_spec
    except Exception as e:
        print(e)


if __name__ == '__main__':
    bench_k8s()
    bench_kopf()
