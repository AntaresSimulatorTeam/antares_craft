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
from dataclasses import asdict
from typing import Any, Optional

from pydantic import Field

from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate, InflowStructure, InflowStructureUpdate
from antares.craft.model.study import STUDY_VERSION_9_2
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.alias_generators import to_kebab
from antares.study.version import StudyVersion

HydroPropertiesType = HydroProperties | HydroPropertiesUpdate
HydroInflowStructureType = InflowStructure | InflowStructureUpdate


class HydroPropertiesLocal(LocalBaseModel):
    inter_daily_breakdown: float = Field(default=1, alias="inter-daily-breakdown")
    intra_daily_modulation: float = Field(default=24, alias="intra-daily-modulation")
    inter_monthly_breakdown: float = Field(default=1, alias="inter-monthly-breakdown")
    reservoir: bool = False
    reservoir_capacity: float = Field(default=0, alias="reservoir capacity")
    follow_load: bool = Field(default=True, alias="follow load")
    use_water: bool = Field(default=False, alias="use water")
    hard_bounds: bool = Field(default=False, alias="hard bounds")
    initialize_reservoir_date: int = Field(default=0, alias="initialize reservoir date")
    use_heuristic: bool = Field(default=True, alias="use heuristic")
    power_to_level: bool = Field(default=False, alias="power to level")
    use_leeway: bool = Field(default=False, alias="use leeway")
    leeway_low: float = Field(default=1, alias="leeway low")
    leeway_up: float = Field(default=1, alias="leeway up")
    pumping_efficiency: float = Field(default=1, alias="pumping efficiency")
    # Introduced in v9.2
    overflow_spilled_cost_difference: Optional[float] = Field(default=None, alias="overflow spilled cost difference")

    @staticmethod
    def get_9_2_fields_and_default_value() -> dict[str, Any]:
        return {"overflow_spilled_cost_difference": 1}

    @staticmethod
    def from_user_model(user_class: HydroPropertiesType) -> "HydroPropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return HydroPropertiesLocal.model_validate(user_dict)

    def to_user_model(self) -> HydroProperties:
        return HydroProperties(
            inter_daily_breakdown=self.inter_daily_breakdown,
            intra_daily_modulation=self.intra_daily_modulation,
            inter_monthly_breakdown=self.inter_monthly_breakdown,
            reservoir=self.reservoir,
            reservoir_capacity=self.reservoir_capacity,
            follow_load=self.follow_load,
            use_water=self.use_water,
            initialize_reservoir_date=self.initialize_reservoir_date,
            use_heuristic=self.use_heuristic,
            power_to_level=self.power_to_level,
            use_leeway=self.use_leeway,
            leeway_low=self.leeway_low,
            leeway_up=self.leeway_up,
            pumping_efficiency=self.pumping_efficiency,
            overflow_spilled_cost_difference=self.overflow_spilled_cost_difference,
        )


def validate_properties_against_version(properties: HydroPropertiesLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_9_2:
        for field in HydroPropertiesLocal.get_9_2_fields_and_default_value():
            check_min_version(properties, field, version)


def initialize_with_version(properties: HydroPropertiesLocal, version: StudyVersion) -> HydroPropertiesLocal:
    if version >= STUDY_VERSION_9_2:
        for field, value in HydroPropertiesLocal.get_9_2_fields_and_default_value().items():
            initialize_field_default(properties, field, value)
    return properties


def parse_hydro_properties_local(study_version: StudyVersion, data: Any) -> HydroProperties:
    local_properties = HydroPropertiesLocal.model_validate(data)
    validate_properties_against_version(local_properties, study_version)
    initialize_with_version(local_properties, study_version)
    return local_properties.to_user_model()


def serialize_hydro_properties_local(
    study_version: StudyVersion, properties: HydroPropertiesType, exclude_unset: bool
) -> dict[str, Any]:
    local_properties = HydroPropertiesLocal.from_user_model(properties)
    validate_properties_against_version(local_properties, study_version)
    return local_properties.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=exclude_unset)


class InterMonthlyCorrelation(LocalBaseModel, alias_generator=to_kebab):
    intermonthly_correlation: float = 0.5


class HydroInflowStructureLocal(LocalBaseModel):
    prepro: InterMonthlyCorrelation

    @staticmethod
    def from_user_model(user_class: HydroInflowStructureType) -> "HydroInflowStructureLocal":
        return HydroInflowStructureLocal.model_validate(
            {"prepro": {"intermonthly_correlation": user_class.intermonthly_correlation}}
        )

    def to_user_model(self) -> InflowStructure:
        return InflowStructure(intermonthly_correlation=self.prepro.intermonthly_correlation)
