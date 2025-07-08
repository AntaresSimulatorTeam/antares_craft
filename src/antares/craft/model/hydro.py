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
from dataclasses import asdict, dataclass, replace
from typing import Optional

import pandas as pd

from antares.craft.service.base_services import BaseHydroService


@dataclass
class HydroPropertiesUpdate:
    inter_daily_breakdown: Optional[float] = None
    intra_daily_modulation: Optional[float] = None
    inter_monthly_breakdown: Optional[float] = None
    reservoir: Optional[bool] = None
    reservoir_capacity: Optional[float] = None
    follow_load: Optional[bool] = None
    use_water: Optional[bool] = None
    hard_bounds: Optional[bool] = None
    initialize_reservoir_date: Optional[int] = None
    use_heuristic: Optional[bool] = None
    power_to_level: Optional[bool] = None
    use_leeway: Optional[bool] = None
    leeway_low: Optional[float] = None
    leeway_up: Optional[float] = None
    pumping_efficiency: Optional[float] = None
    # Introduced in v9.2
    overflow_spilled_cost_difference: Optional[float] = None


@dataclass(frozen=True)
class HydroProperties:
    inter_daily_breakdown: float = 1
    intra_daily_modulation: float = 24
    inter_monthly_breakdown: float = 1
    reservoir: bool = False
    reservoir_capacity: float = 0
    follow_load: bool = True
    use_water: bool = False
    hard_bounds: bool = False
    initialize_reservoir_date: int = 0
    use_heuristic: bool = True
    power_to_level: bool = False
    use_leeway: bool = False
    leeway_low: float = 1
    leeway_up: float = 1
    pumping_efficiency: float = 1
    # Introduced in v9.2
    overflow_spilled_cost_difference: Optional[float] = None  # default 1

    def from_update_properties(self, update_properties: HydroPropertiesUpdate) -> "HydroProperties":
        current_properties = asdict(self)
        current_properties.update({k: v for k, v in asdict(update_properties).items() if v is not None})
        return HydroProperties(**current_properties)

    def to_update_properties(self) -> HydroPropertiesUpdate:
        return HydroPropertiesUpdate(
            inter_daily_breakdown=self.inter_daily_breakdown,
            intra_daily_modulation=self.intra_daily_modulation,
            inter_monthly_breakdown=self.inter_monthly_breakdown,
            reservoir=self.reservoir,
            reservoir_capacity=self.reservoir_capacity,
            follow_load=self.follow_load,
            use_water=self.use_water,
            hard_bounds=self.hard_bounds,
            initialize_reservoir_date=self.initialize_reservoir_date,
            use_heuristic=self.use_heuristic,
            power_to_level=self.power_to_level,
            use_leeway=self.use_leeway,
            leeway_low=self.leeway_low,
            leeway_up=self.leeway_up,
            pumping_efficiency=self.pumping_efficiency,
            overflow_spilled_cost_difference=self.overflow_spilled_cost_difference,
        )


@dataclass(frozen=True)
class InflowStructure:
    intermonthly_correlation: float = 0.5


@dataclass
class InflowStructureUpdate:
    intermonthly_correlation: float


class Hydro:
    def __init__(
        self, service: BaseHydroService, area_id: str, properties: HydroProperties, inflow_structure: InflowStructure
    ):
        self._area_id = area_id
        self._service = service
        self._properties = properties
        self._inflow_structure = inflow_structure

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def properties(self) -> HydroProperties:
        return self._properties

    @property
    def inflow_structure(self) -> InflowStructure:
        return self._inflow_structure

    def update_properties(self, properties: HydroPropertiesUpdate) -> None:
        self._service.update_properties(self.area_id, properties)
        self._properties = self._properties.from_update_properties(properties)

    def update_inflow_structure(self, inflow_structure: InflowStructureUpdate) -> None:
        self._service.update_inflow_structure(self.area_id, inflow_structure)
        self._inflow_structure = replace(
            self._inflow_structure, intermonthly_correlation=inflow_structure.intermonthly_correlation
        )

    def get_maxpower(self) -> pd.DataFrame:
        return self._service.get_maxpower(self.area_id)

    def get_reservoir(self) -> pd.DataFrame:
        return self._service.get_reservoir(self.area_id)

    def get_inflow_pattern(self) -> pd.DataFrame:
        return self._service.get_inflow_pattern(self.area_id)

    def get_credit_modulations(self) -> pd.DataFrame:
        return self._service.get_credit_modulations(self.area_id)

    def get_water_values(self) -> pd.DataFrame:
        return self._service.get_water_values(self.area_id)

    def get_ror_series(self) -> pd.DataFrame:
        return self._service.get_ror_series(self.area_id)

    def get_mod_series(self) -> pd.DataFrame:
        return self._service.get_mod_series(self.area_id)

    def get_mingen(self) -> pd.DataFrame:
        return self._service.get_mingen(self.area_id)

    def get_energy(self) -> pd.DataFrame:
        return self._service.get_energy(self.area_id)

    def set_maxpower(self, series: pd.DataFrame) -> None:
        return self._service.set_maxpower(self.area_id, series)

    def set_reservoir(self, series: pd.DataFrame) -> None:
        return self._service.set_reservoir(self.area_id, series)

    def set_inflow_pattern(self, series: pd.DataFrame) -> None:
        return self._service.set_inflow_pattern(self.area_id, series)

    def set_credits_modulation(self, series: pd.DataFrame) -> None:
        return self._service.set_credits_modulation(self.area_id, series)

    def set_water_values(self, series: pd.DataFrame) -> None:
        return self._service.set_water_values(self.area_id, series)

    def set_mod_series(self, series: pd.DataFrame) -> None:
        return self._service.set_mod_series(self.area_id, series)

    def set_ror_series(self, series: pd.DataFrame) -> None:
        return self._service.set_ror_series(self.area_id, series)

    def set_mingen(self, series: pd.DataFrame) -> None:
        return self._service.set_mingen(self.area_id, series)

    def set_energy(self, series: pd.DataFrame) -> None:
        return self._service.set_energy(self.area_id, series)
