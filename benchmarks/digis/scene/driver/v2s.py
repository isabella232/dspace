import os
import sys
import cv2
import json
import numpy as np
import pprint as pp
from collections import defaultdict

from video.vcap import VideoCapture
from video.motion import MotionDetect

from scene import SceneStatus
from util import timed, download_url, digest

import ssl


# TBD remove ssl
ssl._create_default_https_context = ssl._create_unverified_context

"""
vid2scene.py takes a video stream, runs one or multiple object 
recognition algorithms, and posts a a scene of objects to the
state store (currently vanilla redis).
"""

# paths
path_join = os.path.join
abs_path = os.path.abspath
_dir_path = os.path.dirname(os.path.realpath(__file__))

# device configs
_dev_dir = abs_path(path_join(_dir_path, ".."))
_dev_config_file = path_join(_dev_dir, "device.json")

# model configs
_ml_dir = abs_path(path_join(_dir_path, "ml"))
_net_weight_file = path_join(_ml_dir, "yolov3.weights")
_net_cfg_file = path_join(_ml_dir, "yolov3.cfg")
_net_class_file = path_join(_ml_dir, "coco.names")
_net_weight_url = "https://digivice.s3-us-west-2.amazonaws.com/yolov3.weights"

# open cv configs
os.environ["OPENCV_FFMPEG_CAPTURE_OPTIONS"] = "rtsp_transport;udp"


class Obj:
    def __init__(self, name=None, position=None):
        self.name = name
        self.position = position

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str(self.to_dict())

    @classmethod
    def from_dict(cls, d):
        return Obj(d["name"], d["position"])

    def to_dict(self):
        return {
            "name": self.name,
            "position": self.position,
        }


class Vid2Scene:
    """ Conversion of a videos stream to a scene of objects.

    Attributes:
        self.run(): entry method, prepares video capture, cv models,
            and the scene object.
        self.detect(frame):  runs obj recognition on a given frame and
            updates the scene object.
    """

    def __init__(self, config: dict):
        assert "url" in config, "vid2scene: missing video stream url"
        assert "id" in config, "vid2scene: missing scene id"

        # meta configs
        self.config = config
        self.debug = config.get("debug", False)
        self.display = config.get("display", False)
        self.gvr = config.get("gvr", None)

        # video capture and motion detect
        self.url = config["url"]
        self.cap_interval = config.get("cap_interval", 1)
        self.vcap = None
        self.md = None

        # ml model states
        self.net = None
        self.classes = list()
        self.output_layers = None
        self.colors = None
        self.conf_thresh = config.get("vid2scene_conf_thresh",
                                      0.5)  # confidence threshold

        # download model weights if not exist
        if not os.path.isfile(_net_weight_file):
            print("vid2scene: missing model weights file, downloading..")
            download_url(_net_weight_url, _net_weight_file)

        # state store
        self.scene = SceneStatus(id_=config["id"])
        self.scene.status = defaultdict(dict)

    @timed
    def _load(self):
        # load classes
        with open(_net_class_file, "r") as f:
            self.classes = [line.strip()
                            for line in f.readlines()]

        # load yolov3 weights and configs;
        self.net = cv2.dnn.readNet(_net_weight_file, _net_cfg_file)

        # config layers
        layer_names = self.net.getLayerNames()
        self.output_layers = [layer_names[i[0] - 1]
                              for i in self.net.getUnconnectedOutLayers()]
        self.colors = np.random.uniform(0, 255,
                                        size=(len(self.classes), 3))

    def run(self):
        if self.debug:
            print("debug:", cv2.getBuildInformation())

        # prep video capture  TODO: try..except..
        self.vcap = VideoCapture(self.url)
        _, frame = self.vcap.read()
        print("vid2scene: video capture started")

        # prep motion detector
        self.md = MotionDetect(ref_frame=frame)

        # model load and prep
        self._load()

        # capture loop
        self._loop()

    def _loop(self):
        # detection loop
        print("vid2obj: loop capturing..")
        while True:
            ret, frame = self.vcap.read()
            if self.debug:
                print("debug:", ret)

            if self.md.moved(frame):
                # on MBP16": motion detection saves ~10x less cpu cycles;
                # self.detect takes ~200ms and model load ~300ms;
                frame = self.detect(frame)

                self.scene.put()

                # XXX: upload should be queued in another thread
                if self.gvr:
                    self.scene.upload(self.gvr)

                if self.debug or self.display:
                    pp.pprint(self.scene)
                if self.display:
                    cv2.imshow("vid2obj", frame)

            cv2.waitKey(self.cap_interval)

    @timed
    def detect(self, frame):
        """Detect objects in the frame and write to self.objs"""
        height, width, channels = frame.shape
        if self.debug:
            print("debug, detect: frame info", height, width, channels)

        blob = cv2.dnn.blobFromImage(frame, 0.00392, (416, 416),
                                     (0, 0, 0), True, crop=False)
        self.net.setInput(blob)
        outs = self.net.forward(self.output_layers)

        # object classifications
        class_ids = []
        confidences = []
        boxes = []
        for out in outs:
            for detection in out:
                scores = detection[5:]
                class_id = np.argmax(scores)
                confidence = scores[class_id]

                if confidence > self.conf_thresh:
                    # Object detected
                    center_x = int(detection[0] * width)
                    center_y = int(detection[1] * height)
                    w = int(detection[2] * width)
                    h = int(detection[3] * height)

                    # Rectangle coordinates
                    x = int(center_x - w / 2)
                    y = int(center_y - h / 2)
                    boxes.append([x, y, w, h])

                    confidences.append(float(confidence))
                    class_ids.append(class_id)

        # non maximum suppression, remove extra boxes for the same object
        indexes = cv2.dnn.NMSBoxes(boxes, confidences, 0.5, 0.4)

        # empty the scene
        self.scene.status = defaultdict(list)

        # parse results as scene
        for i in range(len(boxes)):
            if i in indexes:
                label = str(self.classes[class_ids[i]])

                # display configs
                x, y, w, h = boxes[i]
                color = self.colors[i]
                cv2.rectangle(frame, (x, y), (x + w, y + h), color, 2)
                cv2.putText(frame, label, (x, y + 30),
                            cv2.FONT_HERSHEY_PLAIN, 3, color, 3)

                # add object to the scene
                o = Obj(name=label, position=boxes[i])
                self.scene.status[label].append(o.to_dict())
        return frame


def new_vid2scene_from_config(_id):
    with open(_dev_config_file) as f:
        config = json.load(f)

    if _id not in config:
        print(f"abort: make sure the test id {_id} exist")
        return

    return Vid2Scene(config=config[_id])


def new_vid2scene_from_config_str(config: str):
    config = json.loads(config)

    config = {
        "provider": "",
        "kind": "vid",
        "url": config["url"],
        "id": digest(config["url"]),
        "display": False,
    }

    return Vid2Scene(config=config)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        v2s = new_vid2scene_from_config_str(sys.argv[1])  # url
    else:
        v2s = new_vid2scene_from_config("kome-vid-wyze")
    try:
        sys.exit(v2s.run())
    except KeyboardInterrupt:
        sys.exit('\nInterrupted')
