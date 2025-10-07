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

from pydantic import Field

from antares.craft import ScenarioBuilder
from antares.craft.model.commons import STUDY_VERSION_9_2, STUDY_VERSION_9_3
from antares.craft.model.scenario_builder import (
    ScenarioArea,
    ScenarioCluster,
    ScenarioConstraint,
    ScenarioHydroLevel,
    ScenarioLink,
    ScenarioMatrix,
    ScenarioMatrixHydro,
    ScenarioStorage,
    ScenarioStorageConstraints,
    get_default_builder_matrix,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.study.version import StudyVersion


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
    hydro_initial_level: dict[str, dict[str, float]] = Field(alias="hl")
    hydro_generation_power: dict[str, dict[str, int]] = Field(alias="hgp")
    hydro_final_level: dict[str, dict[str, float]] = Field(alias="hfl")
    storage_inflows: dict[str, dict[str, dict[str, int]]] = Field(alias="sts")
    storage_constraints: dict[str, dict[str, dict[str, dict[str, int]]]] = Field(alias="sta")

    @staticmethod
    def from_api(data: dict[str, Any]) -> "ScenarioBuilderAPI":
        scenario_api = data["Default Ruleset"]
        return ScenarioBuilderAPI.model_validate(scenario_api)

    def to_api(self) -> dict[str, Any]:
        return {"Default Ruleset": self.model_dump(by_alias=True, exclude_none=True)}

    def to_user_model(self, nb_years: int, study_version: StudyVersion) -> ScenarioBuilder:
        scenario_builder = ScenarioBuilder(
            load=ScenarioArea(_data={}, _years=nb_years),
            thermal=ScenarioCluster(_data={}, _years=nb_years),
            hydro=ScenarioArea(_data={}, _years=nb_years),
            wind=ScenarioArea(_data={}, _years=nb_years),
            solar=ScenarioArea(_data={}, _years=nb_years),
            link=ScenarioLink(_data={}, _years=nb_years),
            renewable=ScenarioCluster(_data={}, _years=nb_years),
            binding_constraint=ScenarioConstraint(_data={}, _years=nb_years),
            hydro_initial_level=ScenarioHydroLevel(_data={}, _years=nb_years),
            hydro_generation_power=ScenarioArea(_data={}, _years=nb_years),
        )
        if study_version >= STUDY_VERSION_9_2:
            scenario_builder.hydro_final_level = ScenarioHydroLevel(_data={}, _years=nb_years)
        if study_version >= STUDY_VERSION_9_3:
            scenario_builder.storage_inflows = ScenarioStorage(_data={}, _years=nb_years)
            scenario_builder.storage_constraints = ScenarioStorageConstraints(_data={}, _years=nb_years)

        for keyword in [
            "load",
            "solar",
            "wind",
            "hydro",
            "hydro_generation_power",
            "link",
            "binding_constraint",
        ]:
            user_dict: dict[str, ScenarioMatrix] = {}
            attribute = getattr(self, keyword)
            if not attribute:
                continue
            for key, value in attribute.items():
                user_dict[key] = get_default_builder_matrix(nb_years)
                for mc_year, ts_year in value.items():
                    user_dict[key]._matrix[int(mc_year)] = ts_year
            field_value: ScenarioArea | ScenarioLink | ScenarioConstraint = ScenarioArea(
                _data=user_dict, _years=nb_years
            )
            if keyword == "link":
                field_value = ScenarioLink(_data=user_dict, _years=nb_years)
            elif keyword == "binding_constraint":
                field_value = ScenarioConstraint(_data=user_dict, _years=nb_years)
            setattr(scenario_builder, keyword, field_value)

        for keyword in ["hydro_initial_level", "hydro_final_level"]:
            user_dict_hydro: dict[str, ScenarioMatrixHydro] = {}
            attribute = getattr(self, keyword)
            if not attribute:
                continue
            for key, value in attribute.items():
                user_dict_hydro[key] = ScenarioMatrixHydro([None] * nb_years)
                for mc_year, level_value in value.items():
                    user_dict_hydro[key]._matrix[int(mc_year)] = level_value
            setattr(scenario_builder, keyword, ScenarioHydroLevel(_data=user_dict_hydro, _years=nb_years))

        for keyword in ["renewable", "thermal", "storage_inflows"]:
            data_dict: dict[str, dict[str, ScenarioMatrix]] = {}
            attribute = getattr(self, keyword)
            if not attribute:
                continue
            for area_id, value in attribute.items():
                data_dict[area_id] = {}
                for obj_id, values in value.items():
                    data_dict[area_id][obj_id] = get_default_builder_matrix(nb_years)
                    for mc_year, ts_year in values.items():
                        data_dict[area_id][obj_id]._matrix[int(mc_year)] = ts_year
            scenario_class = ScenarioStorage if keyword == "storage_inflows" else ScenarioCluster
            setattr(scenario_builder, keyword, scenario_class(_data=data_dict, _years=nb_years))

        if self.storage_constraints:
            sts_constraints_dict: dict[str, dict[str, dict[str, ScenarioMatrix]]] = {}
            for area_id, value in self.storage_constraints.items():
                sts_constraints_dict[area_id] = {}
                for sts_id, values in value.items():
                    sts_constraints_dict[area_id][sts_id] = {}
                    for constraint_id, inner_values in values.items():
                        sts_constraints_dict[area_id][sts_id][constraint_id] = get_default_builder_matrix(nb_years)
                        for mc_year, ts_year in inner_values.items():
                            sts_constraints_dict[area_id][sts_id][constraint_id]._matrix[int(mc_year)] = ts_year

            scenario_builder.storage_constraints = ScenarioStorageConstraints(
                _data=sts_constraints_dict, _years=nb_years
            )

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
            "hydro_final_level",
            "hydro_generation_power",
            "link",
            "binding_constraint",
        ]:
            attribute = getattr(user_class, keyword)
            if not attribute:
                continue
            api_data = {}
            for area_id, values in attribute._data.items():
                api_data[area_id] = {str(index): value for index, value in enumerate(values._matrix) if value}
            args[keyword] = api_data

        for keyword in ["renewable", "thermal", "storage_inflows"]:
            attribute = getattr(user_class, keyword)
            if not attribute:
                continue
            obj_api_data: dict[str, dict[str, dict[str, int]]] = {}
            for area_id, value in attribute._data.items():
                obj_api_data[area_id] = {}
                for obj_id, scenario_matrix in value.items():
                    obj_data = {str(index): value for index, value in enumerate(scenario_matrix._matrix) if value}
                    obj_api_data[area_id][obj_id] = obj_data
            args[keyword] = obj_api_data

        if user_class.storage_constraints:
            api_sts_data: dict[str, dict[str, dict[str, dict[str, int]]]] = {}
            for area_id, value in user_class.storage_constraints._data.items():
                api_sts_data[area_id] = {}
                for sts_id, values in value.items():
                    api_sts_data[area_id][sts_id] = {}
                    for constraint_id, scenario_matrix in values.items():
                        sts_data = {str(index): value for index, value in enumerate(scenario_matrix._matrix) if value}
                        api_sts_data[area_id][sts_id][constraint_id] = sts_data
            args["storage_constraints"] = api_sts_data

        return ScenarioBuilderAPI.model_validate(args)
