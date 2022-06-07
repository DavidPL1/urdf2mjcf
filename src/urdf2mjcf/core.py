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


def abspath_from_ros_uri(uri: str, rospack: RosPack = None) -> str:
    """Parse a ROS package URI into an absolute path"""
    rospack = RosPack() if rospack is None else rospack

    scheme, netloc, path, *_ = urlparse(uri)

    assert scheme == "package", f"Got URI that is not of scheme 'package': {scheme}"

    package = Path(rospack.get_path(netloc))
    relative_path = Path(path if path[0] != "/" else path[1:])

    assert (
        not relative_path.is_absolute()
    ), f"Asset path is not relative: {relative_path}"

    assert (
        package / relative_path
    ).is_absolute(), f"Resolved path is not abosulte: {package / relative_path}"

    return str(package / relative_path)


def resolve_ros_uris(urdf: Element, rospack: RosPack = None) -> None:
    """Resolve all collision mesh ROS package URIs to absolute paths"""
    for mesh_node in urdf.findall(".//collision/*/mesh[@filename]"):

        ros_uri = mesh_node.get("filename", None)
        assert (
            ros_uri is not None
        ), f"Mesh node without filename: '{mesh_node.tag}' : {mesh_node.attrib}"

        absolute_path = abspath_from_ros_uri(ros_uri, rospack)

        mesh_node.set("filename", absolute_path)


def populate_sensors(mjcf: Element, sensor_config: Element) -> None:
    """Add sites and sensors to an MJCF object"""
    for body_node in sensor_config.findall("./body"):
        body_name = body_node.get("name", None)
        assert (
            body_name is not None
        ), f"Bad sensorconfig.; body node has no name ({body_node.attrib})"

        body_in_mjcf = mjcf.find(f".//body[@name='{body_name}']")
        assert body_in_mjcf is not None, f"No body in MJCF with name '{body_name}'"

        body_in_mjcf.extend(body_node.findall("./site"))

    mjcf.extend(sensor_config.findall("./sensor"))


