#!/usr/bin/env python3

import os
import sys
import yaml
import inflection

"""
Generate dSpace CRD from templates and configuration file (model.yaml).

TBD: a principled version from k8s code generators.
"""

_header = """
apiVersion: apiextensions.k8s.io/v1
kind: CustomResourceDefinition
metadata:
  name: {name}
spec:
  group: {group}
  names:
    kind: {kind}
    listKind: {kind}List
    plural: {plural}
    singular: {singular}
  scope: Namespaced
  versions:
"""

_version_spec = """
name: {version}
schema:
  openAPIV3Schema:
    properties:
      apiVersion:
        type: string
      kind:
        type: string
      metadata:
        type: object
      spec:
        properties: 
        type: object
    type: object
served: true
storage: true
"""

_control = """
control:
  properties: 
  type: object
"""

_control_attr = """
properties:
  intent:
    type: {datatype} 
  status:
    type: {datatype}
type: object
"""

_data = """
data:
  properties:
    input:
      properties:
      type: object
    output:
      properties:
      type: object
  type: object
"""

_data_attr = """
    TBD
"""

_obs = """
obs:
  properties:
  type: object
"""

_obs_attr = """
type: {datatype}
"""

_mount = """
mount:
  properties:
  type: object
"""

_mount_attr = """
additionalProperties:
  properties:
    mode:
      type: string
    status:
      type: string
  type: object
type: object
"""


def plural(model):
    return inflection.pluralize(model["kind"]).lower()


def gen(name):
    _dir_path = os.path.join(os.path.dirname(os.path.realpath(__file__)), name)

    with open(os.path.join(_dir_path, "model.yaml")) as f:
        model = yaml.load(f, Loader=yaml.FullLoader)

        # assemble the crd
        header = _header.format(name=plural(model) + "." + model["group"],
                                group=model["group"],
                                kind=model["kind"],
                                plural=plural(model),
                                singular=model["kind"].lower())
        header = yaml.load(header, Loader=yaml.FullLoader)

        # attributes
        def make_root_attr(name, _attr_tpl, _main_tpl):
            attrs, result = dict(), dict()
            for _n, t in model.get(name, {}).items():
                if type(t) is not str:
                    assert type(t) is dict and "openapi" in t
                    attrs[_n] = t["openapi"]
                else:
                    attrs[_n] = yaml.load(_attr_tpl.format(name=_n, datatype=t), Loader=yaml.FullLoader)
            if len(attrs) > 0:
                result = yaml.load(_main_tpl, Loader=yaml.FullLoader)
                result[name]["properties"] = attrs
            return result

        control = make_root_attr("control", _control_attr, _control)
        data = make_root_attr("data", _data_attr, _data)
        obs = make_root_attr("obs", _obs_attr, _obs)
        mount = make_root_attr("mount", _mount_attr, _mount)

        # assert not (len(control) > 0 and len(data) > 0)

        # version
        version = _version_spec.format(version=model["version"])
        version = yaml.load(version, Loader=yaml.FullLoader)
        spec = version["schema"]["openAPIV3Schema"]["properties"]["spec"]
        spec["properties"] = dict()
        spec["properties"].update(control)
        spec["properties"].update(data)
        spec["properties"].update(obs)
        spec["properties"].update(mount)

        # main TBD: multiple version or incremental versions
        header["spec"]["versions"] = list()
        header["spec"]["versions"].append(version)

        crd = header

        with open(os.path.join(_dir_path, "crd.yaml"), "w") as f:
            yaml.dump(crd, f)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        gen(sys.argv[1])
    else:
        gen("sample")
