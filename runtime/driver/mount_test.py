import os
import sys
import subprocess
import time
import yaml
import inflection

_dir = os.path.dirname(os.path.realpath(__file__))
_mock_dir = os.path.join(_dir, "..", "mocks")
_parent_cr = os.path.join(_mock_dir, "room", "test", "cr.yaml")
_child_cr = os.path.join(_mock_dir, "lamp", "test", "cr.yaml")


def _wait(t=0.5):
    time.sleep(t)


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
"""


def test_mount(parent, child):
    _make_cr(parent)
    _show(parent)

    _make_cr(child)
    _show(child)

    _wait()
    _mount(child, parent)

    _wait()
    _show(parent)
    _wait(t=10)


def test_prop(parent, child):
    pass


# TBD move to pytest
def test_all():
    with _Setup() as s:
        test_mount(s.parent, s.child)

    with _Setup() as s:
        test_prop(s.parent, s.child)


class _Setup:
    @staticmethod
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
                "cr_file": cr,
            }

    def __enter__(self):
        self.parent = self._parse(_parent_cr)
        self.child = self._parse(_child_cr)

        _make_cr(self.parent, delete=True)
        _make_cr(self.child, delete=True)

        _cmd(f"dq alias {self.parent['auri']} {self.parent['alias']}")
        _cmd(f"dq alias {self.child['auri']} {self.child['alias']}")
        return self

    def __exit__(self, *args, **kwargs):
        _make_cr(self.parent, delete=True)
        _make_cr(self.child, delete=True)


def _mount(child, parent, unmount=False):
    _cmd(f"dq mount {'-d ' if unmount else ''}"
         f"{child['alias']} {parent['alias']}",
         show_cmd=True)


def _make_driver(kind):
    _cmd(f"cd {_mock_dir}; KIND={kind} make test")


def _make_cr(model, delete=False):
    _cmd(f"kubectl {'delete' if delete else 'apply'} "
         f"-f {model['cr_file']} "
         f"{'> /dev/null 2>&1 | true' if delete else ''}")


def _show(model, neat=True):
    print("---")
    _cmd(f"kubectl get {model['k']} {model['n']} "
         f"-oyaml {'| kubectl neat' if neat else ''}")


def _cmd(cmd, show_cmd=False, quiet=False):
    """Executes a subprocess running a shell command and
    returns the output."""
    if show_cmd:
        print()
        print("$", cmd)

    if quiet:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            shell=True,
            executable='/bin/bash')
    else:
        proc = subprocess.Popen(cmd, shell=True,
                                executable='/bin/bash')

    out, _ = proc.communicate()

    if proc.returncode:
        if quiet:
            print('Log:\n', out, file=sys.stderr)
        print('Error has occurred running command: %s' % cmd,
              file=sys.stderr)
        sys.exit(proc.returncode)
    return out


if __name__ == '__main__':
    test_all()
