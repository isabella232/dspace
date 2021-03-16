import os
import sys
import subprocess
import yaml
import inflection

from kubernetes import client, config
from kubernetes.client.rest import ApiException

import util

config.load_kube_config()

_dir = os.path.dirname(os.path.realpath(__file__))
_mock_dir = os.path.join(_dir, "..", "mocks")
_parent_cr = os.path.join(_mock_dir, "room", "test", "cr.yaml")
_child_cr = os.path.join(_mock_dir, "lamp", "test", "cr.yaml")

# seconds to wait for event propagation
_wait = 0.5

"""
Mount tests:

Create/resume/delete events:
1. create parent model; neat display parent -> parent
2. create child model; neat display child -> child
3. dq mount child parent; neat display parent and child:
    - parent.mount.child
    - parent.mount.child.status matches child.status
    - child.intent matches parent.mount.child.intent
4. dq mount -d child parent; neat display parent and child:
    - parent.mount.child is gone
5. dq mount child parent; kc remove child model; neat display parent
    - parent.mount.child is gone 
6. create child model; neat display parent and child
    - same as 3.
7. delete child model
    - same as 5.

Update events:
1. create parent and child model
2. dq mount child parent
3. update parent.mount.child.intent
    - child.intent matches 
4. update parent.mount.child.status
    - child.status doesn't match
5. update child.status  
    - parent.mount.child.status matches
6. update child.intent
    - parent.mount.child.intent matches

Intent/status/data propagation in digi-graph:
- Each digivice/lake driver writes to its own model;
- The runtime (mounter) propagates updates by writing what's in the source model 
to the target model; this includes intent/status/input/output/obs attributes.
- The runtime (apiserver) implements optimistic concurrency to achieve model-level 
atomic RMW. Each write request carries a version number; upon receiving the 
request, the runtime checks if the version number matches the current version 
number of the model and accepts the request only if so. The version number is 
changed upon each model update -- typically incremented to a larger value.
- Besides version number, each model has a generation number. The 
number is incremented by one upon changes;

When a child model is mounted to a parent model, the parent keeps a copy of 
the child's model under its mount attribute. Synced by the mounter, this copy 
is eventually consistent with the child's model.
- When the parent 

"""


def test_mount():
    _setup()
    _make_cr(_parent_cr)
    _make_cr(_child_cr)


def test_bp():
    pass


# XXX move to pytest
def test_all():
    _setup()
    test_mount()


def _show(model, neat=True):
    _cmd(f"kubectl get {model['k']} {model['n']} "
         f"-oyaml {'| kubectl neat' if neat else ''}")


def _setup():
    def _parse(cr):
        with open(cr) as f:
            model = yaml.load(f, Loader=yaml.SafeLoader)
            meta = model["metadata"]
            auri = "/".join(["", model["apiVersion"], model["kind"],
                             meta.get("namespace", "default"),
                             meta["name"]])
            g, v = model["apiVersion"].split("/")
            return {
                "auri": auri,
                "g": g,
                "v": v,
                "k": model["kind"],
                "n": meta["name"],
                "ns": meta.get("namespace", "default"),
                "r": inflection.pluralize(model["kind"]).lower(),
                "alias": meta["name"],
            }

    parent = _parse(_parent_cr)
    child = _parse(_child_cr)

    _cmd(f"dq alias {parent['auri']} {parent['alias']}")
    _cmd(f"dq alias {child['auri']} {child['alias']}")


def _mount(child_alias, parent_alias, unmount=False):
    _cmd(f"dq mount {'-d ' if unmount else ''}{child_alias} {parent_alias}")


def _make_cr(path, delete=False):
    _cmd(f"kubectl {'delete' if delete else 'apply'} -f {path}")


def _cmd(cmd, quiet=False):
    """Executes a subprocess running a shell command and returns the output."""
    if quiet:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            executable='/bin/bash')
    else:
        proc = subprocess.Popen(cmd, shell=True, executable='/bin/bash')

    out, _ = proc.communicate()

    if proc.returncode:
        if quiet:
            print('Log:\n', out, file=sys.stderr)
        print('Error has occurred running command: %s' % cmd, file=sys.stderr)
        sys.exit(proc.returncode)
    return out


if __name__ == '__main__':
    test_all()
