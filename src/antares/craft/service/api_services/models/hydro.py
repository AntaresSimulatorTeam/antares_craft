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
from typing import Optional

from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate, InflowStructure, InflowStructureUpdate
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

HydroPropertiesType = HydroProperties | HydroPropertiesUpdate
HydroInflowStructureType = InflowStructure | InflowStructureUpdate


@all_optional_model
class HydroPropertiesAPI(APIBaseModel):
    inter_daily_breakdown: float
    intra_daily_modulation: float
    inter_monthly_breakdown: float
    reservoir: bool
    reservoir_capacity: float
    follow_load: bool
    use_water: bool
    hard_bounds: bool
    initialize_reservoir_date: int
    use_heuristic: bool
    power_to_level: bool
    use_leeway: bool
    leeway_low: float
    leeway_up: float
    pumping_efficiency: float
    # Introduced in v9.2
    overflow_spilled_cost_difference: Optional[float] = None

    @staticmethod
    def from_user_model(user_class: HydroPropertiesType) -> "HydroPropertiesAPI":
        user_dict = asdict(user_class)
        return HydroPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> HydroProperties:
        default_properties = HydroProperties()
        return HydroProperties(
            inter_daily_breakdown=self.inter_daily_breakdown or default_properties.inter_daily_breakdown,
            intra_daily_modulation=self.intra_daily_modulation or default_properties.intra_daily_modulation,
            inter_monthly_breakdown=self.inter_monthly_breakdown or default_properties.inter_monthly_breakdown,
            reservoir=self.reservoir or default_properties.reservoir,
            reservoir_capacity=self.reservoir_capacity or default_properties.reservoir_capacity,
            follow_load=self.follow_load or default_properties.follow_load,
            use_water=self.use_water or default_properties.use_water,
            initialize_reservoir_date=self.initialize_reservoir_date or default_properties.initialize_reservoir_date,
            use_heuristic=self.use_heuristic or default_properties.use_heuristic,
            power_to_level=self.power_to_level or default_properties.power_to_level,
            use_leeway=self.use_leeway or default_properties.use_leeway,
            leeway_low=self.leeway_low or default_properties.leeway_low,
            leeway_up=self.leeway_up or default_properties.leeway_up,
            pumping_efficiency=self.pumping_efficiency or default_properties.pumping_efficiency,
            overflow_spilled_cost_difference=self.overflow_spilled_cost_difference,
        )


@all_optional_model
class HydroInflowStructureAPI(APIBaseModel):
    inter_monthly_correlation: float

    @staticmethod
    def from_user_model(user_class: HydroInflowStructureType) -> "HydroInflowStructureAPI":
        return HydroInflowStructureAPI.model_validate(
            {"inter_monthly_correlation": user_class.intermonthly_correlation}
        )

    def to_user_model(self) -> InflowStructure:
        return InflowStructure(
            intermonthly_correlation=self.inter_monthly_correlation or InflowStructure().intermonthly_correlation
        )
