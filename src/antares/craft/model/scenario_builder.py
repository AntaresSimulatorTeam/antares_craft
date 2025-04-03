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
from dataclasses import dataclass
from enum import Enum

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


SYMBOLS_BY_SCENARIO_TYPES = {
    ScenarioType.LOAD: "l",
    ScenarioType.HYDRO: "h",
    ScenarioType.WIND: "w",
    ScenarioType.SOLAR: "s",
    ScenarioType.THERMAL: "t",
    ScenarioType.RENEWABLE: "r",
    ScenarioType.LINK: "ntc",
    ScenarioType.BINDING_CONSTRAINTS: "bc",
    ScenarioType.HYDRO_INITIAL_LEVEL: "hl",
    ScenarioType.HYDRO_FINAL_LEVEL: "hfl",
    ScenarioType.HYDRO_GENERATION_POWER: "hgp",
}


@dataclass
class ScenarioMatrix:
    _matrix: dict[int, int | None]

    def get_year(self, year: int) -> int | None:
        return self._matrix[year]

    def get_scenario(self) -> dict[int, int | None]:
        return self._matrix

    def set_new_scenario(self, new_scenario: dict[int, int | None]) -> None:
        self._matrix = new_scenario


@dataclass
class ScenarioArea:
    _data: dict[str, ScenarioMatrix]

    def get_area(self, area_id: str) -> ScenarioMatrix:
        return self._data[area_id]


@dataclass
class ScenarioConstraint:
    _data: dict[str, ScenarioMatrix]

    def get_group(self, group_id: str) -> ScenarioMatrix:
        return self._data[group_id]


@dataclass
class ScenarioLink:
    _data: dict[str, ScenarioMatrix]

    def get_link(self, link_id: str) -> ScenarioMatrix:
        return self._data[link_id]


@dataclass
class ScenarioCluster:
    _data: dict[str, dict[str, ScenarioMatrix]]

    def get_cluster(self, area_id: str, cluster_id: str) -> ScenarioMatrix:
        return self._data[area_id][cluster_id]


@dataclass
class ScenarioBuilder:
    load: ScenarioArea
    thermal: ScenarioCluster
    hydro: ScenarioArea
    wind: ScenarioArea
    solar: ScenarioArea
    link: ScenarioLink
    renewable: ScenarioCluster
    binding_constraint: ScenarioConstraint
    hydro_initial_level: ScenarioArea
    hydro_generation_power: ScenarioArea
