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

import re

from enum import Enum
from typing import Any, Optional

from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from pydantic import BaseModel
from typing_extensions import override

# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str) -> str:
    """
    Transform a name into an identifier.
    This method is used in AntaresWeb to construct their ids.
    """
    return _sub_invalid_chars(" ", name).strip().lower()


class EnumIgnoreCase(Enum):
    @classmethod
    @override
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

    layerColor: dict[str, str]
    layerX: dict[str, float]
    layerY: dict[str, float]
    ui: MapResponse

    def to_craft(self) -> dict[str, Any]:
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
