""" This is a mock CLI for sending requests for benchmarks. """

import time

import kopf
import digi.util as util

parent = ("bench.digi.dev", "v1", "room")
child = ("bench.digi.dev", "v1", "lamp")

global start


# TBD
def send_request():
    global start
    start = time.time()
    # util.patch_spec(...)


@kopf.on.update(*parent)
def mark_end():
    lat = time.time() - start


def main():
    pass


if __name__ == '__main__':
    main()
