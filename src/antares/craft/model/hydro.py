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
from typing import Optional

import pandas as pd

from antares.craft.service.base_services import BaseHydroService


class HydroMatrixName(Enum):
    SERIES_ROR = "ror"
    SERIES_MOD = "mod"
    SERIES_MIN_GEN = "mingen"
    PREPRO_ENERGY = "energy"
    COMMON_WATER_VALUES = "waterValues"
    COMMON_RESERVOIR = "reservoir"
    COMMON_MAX_POWER = "maxpower"
    COMMON_INFLOW_PATTERN = "inflowPattern"
    COMMON_CREDIT_MODULATIONS = "creditmodulations"


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


@dataclass
class HydroPropertiesUpdate:
    inter_daily_breakdown: Optional[float] = None
    intra_daily_modulation: Optional[float] = None
    inter_monthly_breakdown: Optional[float] = None
    reservoir: Optional[bool] = None
    reservoir_capacity: float = 0
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


class Hydro:
    def __init__(self, service: BaseHydroService, area_id: str, properties: Optional[HydroProperties] = None):
        self._area_id = area_id
        self._service = service
        self._properties = properties or HydroProperties()

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def properties(self) -> HydroProperties:
        return self._properties

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
