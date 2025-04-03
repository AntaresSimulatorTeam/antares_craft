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
from typing import Any

from antares.craft import ScenarioBuilder
from antares.craft.model.scenario_builder import (
    ScenarioArea,
    ScenarioCluster,
    ScenarioConstraint,
    ScenarioLink,
    ScenarioMatrix,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import Field

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
    load: dict[str, dict[str, int]] = Field(alias="l")
    thermal: dict[str, dict[str, dict[str, int]]] = Field(alias="t")
    hydro: dict[str, dict[str, int]] = Field(alias="h")
    wind: dict[str, dict[str, int]] = Field(alias="w")
    solar: dict[str, dict[str, int]] = Field(alias="s")
    link: dict[str, dict[str, int]] = Field(alias="ntc")
    renewable: dict[str, dict[str, dict[str, int]]] = Field(alias="r")
    binding_constraint: dict[str, dict[str, int]] = Field(alias="bc")
    hydro_initial_level: dict[str, dict[str, int]] = Field(alias="hl")
    hydro_generation_power: dict[str, dict[str, int]] = Field(alias="hgp")

    @staticmethod
    def from_api(data: dict[str, Any]) -> "ScenarioBuilderAPI":
        scenario_api = data["Default Ruleset"]
        return ScenarioBuilderAPI.model_validate(scenario_api)

    def to_api(self) -> dict[str, Any]:
        return {"Default Ruleset": self.model_dump(by_alias=True, exclude_none=True)}

    def to_user_model(self, nb_years: int) -> ScenarioBuilder:
        scenario_builder = ScenarioBuilder(
            load=ScenarioArea({}),
            thermal=ScenarioCluster({}),
            hydro=ScenarioArea({}),
            wind=ScenarioArea({}),
            solar=ScenarioArea({}),
            link=ScenarioLink({}),
            renewable=ScenarioCluster({}),
            binding_constraint=ScenarioConstraint({}),
            hydro_initial_level=ScenarioArea({}),
            hydro_generation_power=ScenarioArea({}),
        )

        for keyword in [
            "load",
            "solar",
            "wind",
            "hydro",
            "hydro_initial_level",
            "hydro_generation_power",
            "link",
            "binding_constraint",
        ]:
            user_dict: dict[str, ScenarioMatrix] = {}
            for key, value in getattr(self, keyword).items():
                user_dict[key] = ScenarioMatrix([None] * nb_years)
                for mc_year, ts_year in value.items():
                    user_dict[key]._matrix[int(mc_year)] = ts_year
            field_value: ScenarioArea | ScenarioLink | ScenarioConstraint = ScenarioArea(user_dict)
            if keyword == "link":
                field_value = ScenarioLink(user_dict)
            elif keyword == "binding_constraint":
                field_value = ScenarioConstraint(user_dict)
            setattr(scenario_builder, keyword, field_value)

        for keyword in ["renewable", "thermal"]:
            cluster_dict: dict[str, dict[str, ScenarioMatrix]] = {}
            for area_id, value in getattr(self, keyword).items():
                cluster_dict[area_id] = {}
                for cluster_id, values in value.items():
                    cluster_dict[area_id][cluster_id] = ScenarioMatrix([None] * nb_years)
                    for mc_year, ts_year in value.items():
                        cluster_dict[area_id][cluster_id]._matrix[int(mc_year)] = ts_year
            setattr(scenario_builder, keyword, ScenarioCluster(_data=cluster_dict))

        return scenario_builder

    @staticmethod
    def from_user_model(user_class: ScenarioBuilder) -> "ScenarioBuilderAPI":
        args = {}
        for keyword in [
            "load",
            "solar",
            "wind",
            "hydro",
            "hydro_initial_level",
            "hydro_generation_power",
            "link",
            "binding_constraint",
        ]:
            user_data = getattr(user_class, keyword)._data
            api_data = {str(index): value for index, value in enumerate(user_data)}
            args[keyword] = api_data

        for keyword in ["renewable", "thermal"]:
            cluster_user_data = getattr(user_class, keyword)._data
            cluster_api_data: dict[str, dict[str, dict[str, int]]] = {}
            for area_id, value in cluster_user_data.items():
                cluster_api_data[area_id] = {}
                for cluster_id, scenario_matrix in value.items():
                    cluster_data = {str(index): value for index, value in enumerate(scenario_matrix._matrix)}
                    cluster_api_data[area_id][cluster_id] = cluster_data
            args[keyword] = cluster_api_data
        return ScenarioBuilderAPI.model_validate(args)
