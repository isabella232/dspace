#!/usr/bin/env python3

import os
import sys
import yaml
import inflection
import uuid

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
  type: object
"""
_data_input = """
input:
  properties:
  type: object
"""
_data_output = """
output:
  properties:
  type: object
"""
_data_attr = """
type: {datatype}
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

_cr = """
apiVersion: {groupVersion}
kind: {kind}
metadata:
  name: {name}
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

        # fill in attributes
        def make_attr(_name, _attr_tpl, _main_tpl, src_attrs):
            attrs, result = dict(), dict()
            for _n, t in src_attrs.items():
                if type(t) is not str:
                    assert type(t) is dict and "openapi" in t
                    attrs[_n] = t["openapi"]
                else:
                    attrs[_n] = yaml.load(_attr_tpl.format(name=_n, datatype=t),
                                          Loader=yaml.FullLoader)
            if len(attrs) > 0:
                result = yaml.load(_main_tpl, Loader=yaml.FullLoader)
                result[_name]["properties"] = attrs
            return result

        def make_data_attr():
            _input = make_attr("input", _data_attr, _data_input, src_attrs=model.get("data", {}).get("input", {}))
            _output = make_attr("output", _data_attr, _data_output, src_attrs=model.get("data", {}).get("output", {}))
            if len(_input) + len(_output) == 0:
                return {}
            result = yaml.load(_data, Loader=yaml.FullLoader)
            result["data"]["properties"] = dict()
            result["data"]["properties"].update(_input)
            result["data"]["properties"].update(_output)
            return result

        control = make_attr("control", _control_attr, _control, src_attrs=model.get("control", {}))
        data = make_data_attr()
        obs = make_attr("obs", _obs_attr, _obs, src_attrs=model.get("obs", {}))
        mount = make_attr("mount", _mount_attr, _mount, src_attrs=model.get("mount", {}))

        assert not (len(control) > 0 and len(data) > 0), "cannot have both control and data attrs!"

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

        with open(os.path.join(_dir_path, "crd.yaml"), "w") as f_:
            yaml.dump(crd, f_)

        # generate a CR if missing
        cr_file = os.path.join(_dir_path, "cr.yaml")
        if not os.path.exists(cr_file):
            cr = _cr.format(groupVersion=model["group"] + "/" + model["version"],
                            kind=model["kind"],
                            name=model["kind"].lower() + "-" + str(uuid.uuid4())[:4],
                            )
            cr = yaml.load(cr, Loader=yaml.FullLoader)
            cr["spec"] = dict()

            # XXX improve CR generation
            for _name in ["control", "data", "obs", "mount"]:
                attrs = model.get(_name, {})
                if len(attrs) == 0:
                    continue
                if _name not in cr["spec"]:
                    cr["spec"][_name] = dict()
                for a, _ in attrs.items():
                    cr["spec"][_name].update({a: -1})

            with open(cr_file, "w") as f_:
                yaml.dump(cr, f_)


if __name__ == '__main__':
    if len(sys.argv) > 1:
        gen(sys.argv[1])
    else:
        gen("sample")
