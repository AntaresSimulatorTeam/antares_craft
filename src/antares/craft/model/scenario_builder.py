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
from typing import TYPE_CHECKING

from antares.craft.exceptions.exceptions import InvalidRequestForScenarioBuilder

if TYPE_CHECKING:
    from antares.craft.model.study import Study


@dataclass
class ScenarioMatrix:
    _matrix: list[int | None]

    def get_year(self, year: int) -> int | None:
        return self._matrix[year]

    def get_scenario(self) -> list[int | None]:
        return self._matrix

    def set_new_scenario(self, new_scenario: list[int | None]) -> None:
        self._matrix = new_scenario


@dataclass
class ScenarioMatrixHydro:
    _matrix: list[float | None]

    def get_year(self, year: int) -> float | None:
        return self._matrix[year]

    def get_scenario(self) -> list[float | None]:
        return self._matrix

    def set_new_scenario(self, new_scenario: list[float | None]) -> None:
        self._matrix = new_scenario


def get_default_builder_matrix(nb_years: int) -> ScenarioMatrix:
    return ScenarioMatrix([None] * nb_years)


@dataclass
class ScenarioArea:
    _data: dict[str, ScenarioMatrix]
    _years: int
    _areas: set[str] | None = None

    def get_area(self, area_id: str) -> ScenarioMatrix:
        assert self._areas is not None
        if area_id not in self._areas:
            raise InvalidRequestForScenarioBuilder(f"The area {area_id} does not exist")
        # If the data isn't filled, we fill it before returning
        if area_id not in self._data:
            self._data[area_id] = get_default_builder_matrix(self._years)
        return self._data[area_id]


@dataclass
class ScenarioHydroLevel:
    _data: dict[str, ScenarioMatrixHydro]
    _years: int
    _areas: set[str] | None = None

    def get_area(self, area_id: str) -> ScenarioMatrixHydro:
        assert self._areas is not None
        if area_id not in self._areas:
            raise InvalidRequestForScenarioBuilder(f"The area {area_id} does not exist")
        # If the data isn't filled, we fill it before returning
        if area_id not in self._data:
            self._data[area_id] = ScenarioMatrixHydro([None] * self._years)
        return self._data[area_id]


@dataclass
class ScenarioConstraint:
    _data: dict[str, ScenarioMatrix]
    _years: int
    _groups: set[str] | None = None

    def get_group(self, group_id: str) -> ScenarioMatrix:
        assert self._groups is not None
        if group_id not in self._groups:
            raise InvalidRequestForScenarioBuilder(f"The constraint group {group_id} does not exist")
        # If the data isn't filled, we fill it before returning
        if group_id not in self._data:
            self._data[group_id] = get_default_builder_matrix(self._years)
        return self._data[group_id]


@dataclass
class ScenarioLink:
    _data: dict[str, ScenarioMatrix]
    _years: int
    _links: set[str] | None = None

    def get_link(self, link_id: str) -> ScenarioMatrix:
        assert self._links is not None
        if link_id not in self._links:
            raise InvalidRequestForScenarioBuilder(f"The link {link_id} does not exist")
        # If the data isn't filled, we fill it before returning
        if link_id not in self._data:
            self._data[link_id] = get_default_builder_matrix(self._years)
        return self._data[link_id]


@dataclass
class ScenarioCluster:
    _data: dict[str, dict[str, ScenarioMatrix]]
    _years: int
    _clusters: dict[str, set[str]] | None = None

    def get_cluster(self, area_id: str, cluster_id: str) -> ScenarioMatrix:
        assert self._clusters is not None
        if area_id not in self._clusters:
            raise InvalidRequestForScenarioBuilder(f"The area {area_id} does not exist")
        if cluster_id not in self._clusters[area_id]:
            raise InvalidRequestForScenarioBuilder(f"The cluster {cluster_id} does not exist")
        # If the data isn't filled, we fill it before returning
        if area_id not in self._data:
            self._data[area_id] = {}
        if cluster_id not in self._data[area_id]:
            self._data[area_id][cluster_id] = get_default_builder_matrix(self._years)
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
    hydro_initial_level: ScenarioHydroLevel
    hydro_generation_power: ScenarioArea
    hydro_final_level: ScenarioHydroLevel

    def _set_study(self, study: "Study") -> None:
        areas = study.get_areas()

        area_ids = set(areas.keys())
        self.load._areas = area_ids
        self.wind._areas = area_ids
        self.solar._areas = area_ids
        self.hydro._areas = area_ids
        self.hydro_initial_level._areas = area_ids
        self.hydro_generation_power._areas = area_ids
        self.hydro_final_level._areas = area_ids

        thermal_ids: dict[str, set[str]] = {}
        renewable_ids: dict[str, set[str]] = {}
        for area in areas.values():
            for thermal in area.get_thermals().values():
                thermal_ids.setdefault(thermal.area_id, set()).add(thermal.id)
            for renewable in area.get_renewables().values():
                renewable_ids.setdefault(renewable.area_id, set()).add(renewable.id)
        self.thermal._clusters = thermal_ids
        self.renewable._clusters = renewable_ids

        links = set(study.get_links().keys())
        self.link._links = links

        bc_groups = set()
        for bc in study.get_binding_constraints().values():
            bc_groups.add(bc.properties.group)
        self.binding_constraint._groups = bc_groups
