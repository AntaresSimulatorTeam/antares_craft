# Copyright (c) 2024, RTE (https://www.rte-france.com)
#
# See AUTHORS.txt
#
# This Source Code Form is subject to the terms of the Mozilla Public
# License, v. 2.0. If a copy of the MPL was not distributed with this
# file, You can obtain one at http://mozilla.org/MPL/2.0/.
#
# SPDX-License-Identifier: MPL-2.0
#
# This file is part of the Antares project.

import json
import re

from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional

from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from pydantic import BaseModel

# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str) -> str:
    """
    Transform a name into an identifier.
    This method is used in AntaresWeb to construct their ids.
    """
    return _sub_invalid_chars(" ", name).strip().lower()


def retrieve_file_content(file_to_retrieve: str) -> Dict[str, Any]:
    module_path = Path(__file__).resolve().parent

    path_resources = module_path.parent.parent / "resources"
    path_to_file = path_resources / file_to_retrieve

    with open(path_to_file, "r") as read_content:
        return json.load(read_content)


def transform_ui_data_to_text(data_from_json: Dict[str, Any]) -> str:
    """
    Args:
        data_from_json: ini data to be inserted

    Returns:
        str to be written in .ini file
    """
    ini_content = ""
    for key, value in data_from_json.items():
        if isinstance(value, dict):
            section_header = f"[{key}]"
            ini_content += f"{section_header}\n"
            for inner_key, inner_value in value.items():
                if isinstance(inner_value, list):
                    inner_value_str = " , ".join(map(str, inner_value))
                    ini_content += f"{inner_key} = {inner_value_str}\n"
                else:
                    ini_content += f"{inner_key} = {inner_value}\n"
        else:
            ini_content += f"{key} = {value}\n"

    return ini_content


def extract_content(key: str, file_to_retrieve: str) -> str:
    ini_data = retrieve_file_content(file_to_retrieve)
    data_for_file = ini_data.get(key)
    if data_for_file is not None:
        return transform_ui_data_to_text(data_for_file)
    else:
        raise KeyError(f"Key '{key}' not defined in {file_to_retrieve}")


class EnumIgnoreCase(Enum):
    @classmethod
    def _missing_(cls, value: object) -> Optional["EnumIgnoreCase"]:
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None


class AreaUiResponse(BaseModel):
    """
    Utility class to convert the AntaresWebResponse to Antares-Craft object.
    """

    class MapResponse(BaseModel):
        color_r: int
        color_g: int
        color_b: int
        layers: int
        x: int
        y: int

    layerColor: Dict[str, str]
    layerX: Dict[str, float]
    layerY: Dict[str, float]
    ui: MapResponse

    def to_craft(self) -> Dict[str, Any]:
        json_ui = {
            "layer": self.ui.layers,
            "x": self.ui.x,
            "y": self.ui.y,
            "layer_x": self.layerX,
            "layer_y": self.layerY,
            "layer_color": self.layerColor,
            "color_rgb": [self.ui.color_r, self.ui.color_g, self.ui.color_b],
        }
        return json_ui


# TODO maybe put sorting functions together
def sort_ini_sections(ini_to_sort: CustomRawConfigParser) -> CustomRawConfigParser:
    sorted_ini = CustomRawConfigParser(interpolation=None)
    for section in sorted(ini_to_sort.sections()):
        sorted_ini[section] = ini_to_sort[section]
    return sorted_ini
