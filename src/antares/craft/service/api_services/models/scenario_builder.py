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
from enum import Enum
from typing import Any

from antares.craft import ScenarioBuilder
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

_AREA_RELATED_SYMBOLS = "l", "h", "w", "s", "bc", "hgp"
_LINK_RELATED_SYMBOLS = ("ntc",)
_HYDRO_LEVEL_RELATED_SYMBOLS = "hl", "hfl"
_CLUSTER_RELATED_SYMBOLS = "t", "r"


class ScenarioType(Enum):
    LOAD = "load"
    THERMAL = "thermal"
    HYDRO = "hydro"
    WIND = "wind"
    SOLAR = "solar"
    LINK = "ntc"
    RENEWABLE = "renewable"
    BINDING_CONSTRAINTS = "bindingConstraints"
    HYDRO_INITIAL_LEVEL = "hydroInitialLevels"
    HYDRO_FINAL_LEVEL = "hydroFinalLevels"
    HYDRO_GENERATION_POWER = "hydroGenerationPower"


MAPPING = {
    "l": "load",
    "t": "thermal",
    "h": "hydro",
    "w": "wind",
    "s": "solar",
    "ntc": "link",
    "r": "renewable",
    "bc": "binding_constraint",
    "hl": "hydro_initial_level",
    "hgp": "hydro_generation_power",
}


@all_optional_model
class ScenarioBuilderAPI(APIBaseModel):
    load: dict[str, dict[str, int]]
    thermal: dict[str, dict[str, dict[str, int]]]
    hydro: dict[str, dict[str, int]]
    wind: dict[str, dict[str, int]]
    solar: dict[str, dict[str, int]]
    link: dict[str, dict[str, int]]
    renewable: dict[str, dict[str, dict[str, int]]]
    binding_constraint: dict[str, dict[str, int]]
    hydro_initial_level: dict[str, dict[str, int]]
    hydro_generation_power: dict[str, dict[str, int]]

    @staticmethod
    def from_api(data: dict[str, Any]) -> "ScenarioBuilderAPI":
        args: dict[str, Any] = {}
        # We don't want to look for the ruleset, we assume it's the default one
        scenario_api = data[list(data.keys())[0]]
        for key, value in scenario_api.items():
            if key not in MAPPING:
                raise NotImplementedError(f"Unknown scenario type {key}")
            args[MAPPING[key]] = value
        return ScenarioBuilderAPI.model_validate(args)

    def to_api(self) -> dict[str, Any]:
        pass

    def to_user_model(self) -> ScenarioBuilder:
        pass

    @staticmethod
    def from_user_model(user_class: ScenarioBuilder) -> "ScenarioBuilderAPI":
        pass


web_response = {
    "l": {"area1": {"0": 1}},
    "ntc": {"area1 / area2": {"1": 23}},
    "t": {"area1": {"thermal": {"1": 2}}},
    "hl": {"area1": {"0": 75}},
}
