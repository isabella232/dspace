import json
import redis

from util import timed
from k8s import update_status

# singleton redis client
# TBD: store on api server not redis
_r = redis.StrictRedis(host="localhost")


class SceneStatus:
    """ Schema and client to scene status.

    Attributes:
        self.put(): commit the scene object to state store

        self.get(): retrieve the scene object from state store

        self.__init__(id_): id_ is a required field to discourage
            unnamed scene pollute the state store.
    """

    def __init__(self, id_, status=None):
        # id of the scene; should be unique
        self.id = id_

        # status; loose schema; should include to_dict()
        self.status = status

        # redis client
        self.r = _r

    def __str__(self):
        return self.__repr__()

    def __repr__(self):
        return str(self.to_dict())

    def key(self):
        return self.id

    @timed
    def put(self):
        self.r.set(self.key(), json.dumps(self.to_dict()))

    @timed
    def get(self, raw=False):
        v = self.r.get(self.key())
        if not raw:
            v = json.loads(v)
        return v

    @timed
    def upload(self, gvr):
        # translate status
        status = self.status
        print(status)
        update_status(gvr, status)

    def to_dict(self):
        return {
            "id": self.id,
            "status": self.status,
        }
