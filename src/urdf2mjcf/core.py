""" TODO: add module description """

# Copyright (c) 2022 Fraunhofer IPA; see bottom of this file for full license

from xml.etree.ElementTree import Element, tostring, SubElement
from pathlib import Path
from typing import Union, IO, AnyStr
from os import fdopen, unlink
from tempfile import mkstemp

from defusedxml.ElementTree import parse
from mujoco import MjModel, mj_saveLastXML


def _parse_element(source: Union[str, Path, IO[AnyStr], None], **kwargs) -> Element:
    """Parse source into a Python XML element object, safely"""
    return None if source is None else parse(source, **kwargs).getroot()  # type: ignore


def pass_through_mujoco(model_xml: Element) -> Element:
    """Load and export XML element object through MuJoCo"""
    parsed_model = MjModel.from_xml_string(tostring(model_xml, encoding="unicode"))

    tmp_file_descriptor, tmp_file_name = mkstemp(prefix="tmp_mjcf_", suffix=".xml")
    mj_saveLastXML(tmp_file_name, parsed_model)

    with fdopen(tmp_file_descriptor, "r") as tmp_file:
        backloaded_model_xml = _parse_element(tmp_file)

    unlink(tmp_file_name)

    return backloaded_model_xml


def add_mujoco_node(urdf: Element, mujoco_node: Element = None) -> None:
    """Add the mujoco node to a URDF object"""
    if mujoco_node is None:
        mujoco_node = Element("mujoco")

        compiler_attrib = {
            "strippath": "false",
            "fusestatic": "false",
            "discardvisual": "true",
        }
        compiler_node = SubElement(mujoco_node, "compiler", compiler_attrib)
        lengthrange_node = SubElement(compiler_node, "lengthrange")

        option_node = SubElement(mujoco_node, "option")
        flag_node = SubElement(option_node, "flag")

        size_node = SubElement(mujoco_node, "size")

    urdf.append(mujoco_node)

