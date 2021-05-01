import random
import time
import kopf

from digi.util import patch_spec, get_spec

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


if __name__ == '__main__':
    start = time.time()
    intent = random.randint(1, 100000000)
    put_start = time.time()
    send_request(room, {
        "control": {
            "brightness": {
                "intent": intent,
            }
        }
    })
    print("put time:", time.time() - put_start)
    while True:
        # get_start = time.time()
        s, _, _ = get_spec(*room)
        # print("get time:", time.time() - get_start)
        if s["control"]["brightness"]["intent"] == intent:
            print("done time:", time.time() - start)

