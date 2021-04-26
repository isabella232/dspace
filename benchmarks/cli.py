""" This is a mock CLI for sending requests for benchmarks. """

import time

import kopf
import digi.util as util

parent = ("bench.digi.dev", "v1", "room", "default", "room-test")
child = ("bench.digi.dev", "v1", "lamp", "default", "lamp-test")
child_data = ("bench.digi.dev", "v1", "cam", "default", "cam-test")
child_lake = ("bench.digi.dev", "v1", "scene", "default", "scene-test")

global start


# TBD
def send_request():
    global start
    start = time.time()
    util.patch_spec(...)


@kopf.on.update(*parent[:3])
def mark_end():
    lat = time.time() - start


@kopf.on.update(*child[:3])
def mark_end():
    lat = time.time() - start


@kopf.on.update(*child_data[:3])
def mark_end():
    lat = time.time() - start


@kopf.on.update(*child_lake[:3])
def mark_end():
    lat = time.time() - start


def benchmark():
    send_request()
    pass


if __name__ == '__main__':
    benchmark()
