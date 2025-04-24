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

from pydantic import Field

from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate, InflowStructure, InflowStructureUpdate
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab

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
        )


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
