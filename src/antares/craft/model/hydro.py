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


@dataclass
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
        )


class Hydro:
    def __init__(self, service: BaseHydroService, area_id: str, properties: HydroProperties):
        self._area_id = area_id
        self._service = service
        self._properties = properties

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def properties(self) -> HydroProperties:
        return self._properties

    def update_properties(self, properties: HydroPropertiesUpdate) -> None:
        self._service.update_properties(self.area_id, properties)
        self._properties = self.read_properties()

    def read_properties(self) -> HydroProperties:
        properties = self._service.read_properties(self.area_id)
        self._properties = properties
        return properties

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

    def update_maxpower(self, series: pd.DataFrame) -> None:
        return self._service.update_maxpower(self.area_id, series)

    def update_reservoir(self, series: pd.DataFrame) -> None:
        return self._service.update_reservoir(self.area_id, series)

    def update_inflow_pattern(self, series: pd.DataFrame) -> None:
        return self._service.update_inflow_pattern(self.area_id, series)

    def update_credits_modulation(self, series: pd.DataFrame) -> None:
        return self._service.update_credits_modulation(self.area_id, series)

    def update_water_values(self, series: pd.DataFrame) -> None:
        return self._service.update_water_values(self.area_id, series)

    def update_mod_series(self, series: pd.DataFrame) -> None:
        return self._service.update_mod_series(self.area_id, series)

    def update_ror_series(self, series: pd.DataFrame) -> None:
        return self._service.update_ror_series(self.area_id, series)

    def update_mingen(self, series: pd.DataFrame) -> None:
        return self._service.update_mingen(self.area_id, series)

    def update_energy(self, series: pd.DataFrame) -> None:
        return self._service.update_energy(self.area_id, series)
