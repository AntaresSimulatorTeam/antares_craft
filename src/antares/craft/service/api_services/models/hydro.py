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
from typing import Any

from antares.craft.model.hydro import (
    HydroAllocation,
    HydroProperties,
    HydroPropertiesUpdate,
    InflowStructure,
    InflowStructureUpdate,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel

HydroPropertiesType = HydroProperties | HydroPropertiesUpdate
HydroInflowStructureType = InflowStructure | InflowStructureUpdate


class HydroPropertiesAPI(APIBaseModel):
    inter_daily_breakdown: float | None = None
    intra_daily_modulation: float | None = None
    inter_monthly_breakdown: float | None = None
    reservoir: bool | None = None
    reservoir_capacity: float | None = None
    follow_load: bool | None = None
    use_water: bool | None = None
    hard_bounds: bool | None = None
    initialize_reservoir_date: int | None = None
    use_heuristic: bool | None = None
    power_to_level: bool | None = None
    use_leeway: bool | None = None
    leeway_low: float | None = None
    leeway_up: float | None = None
    pumping_efficiency: float | None = None
    # Introduced in v9.2
    overflow_spilled_cost_difference: float | None = None

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


class HydroInflowStructureAPI(APIBaseModel):
    inter_monthly_correlation: float | None = None

    @staticmethod
    def from_user_model(user_class: HydroInflowStructureType) -> "HydroInflowStructureAPI":
        return HydroInflowStructureAPI.model_validate(
            {"inter_monthly_correlation": user_class.intermonthly_correlation}
        )

    def to_user_model(self) -> InflowStructure:
        return InflowStructure(
            intermonthly_correlation=self.inter_monthly_correlation or InflowStructure().intermonthly_correlation
        )


def parse_hydro_allocation_api(data: dict[str, Any]) -> list[HydroAllocation]:
    allocations = []
    allocations_api = data["allocation"]
    for allocation_api in allocations_api:
        allocations.append(HydroAllocation(area_id=allocation_api["areaId"], coefficient=allocation_api["coefficient"]))
    return allocations


def serialize_hydro_allocation_api(data: list[HydroAllocation]) -> dict[str, Any]:
    allocations = [{"areaId": allocation.area_id, "coefficient": allocation.coefficient} for allocation in data]
    return {"allocation": allocations}
