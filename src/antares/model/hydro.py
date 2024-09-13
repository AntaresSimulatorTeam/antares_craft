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

from enum import Enum
from typing import Optional, Dict, Any

import pandas as pd
from pydantic import BaseModel, computed_field
from pydantic.alias_generators import to_camel

from antares.tools.ini_tool import check_if_none


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


class HydroProperties(
    BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel
):
    """
    Properties of hydro system read from the configuration files.

    All aliases match the name of the corresponding field in the INI files.
    """

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


class HydroPropertiesLocal(BaseModel):
    def __init__(
        self,
        area_id: str,
        hydro_properties: Optional[HydroProperties] = None,
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        self._area_id = area_id
        hydro_properties = hydro_properties or HydroProperties()
        self._inter_daily_breakdown = check_if_none(
            hydro_properties.inter_daily_breakdown, 1
        )
        self._intra_daily_modulation = check_if_none(
            hydro_properties.intra_daily_modulation, 24
        )
        self._inter_monthly_breakdown = check_if_none(
            hydro_properties.inter_monthly_breakdown, 1
        )
        self._reservoir = check_if_none(hydro_properties.reservoir, False)
        self._reservoir_capacity = check_if_none(hydro_properties.reservoir_capacity, 0)
        self._follow_load = check_if_none(hydro_properties.follow_load, True)
        self._use_water = check_if_none(hydro_properties.use_water, False)
        self._hard_bounds = check_if_none(hydro_properties.hard_bounds, False)
        self._initialize_reservoir_date = check_if_none(
            hydro_properties.initialize_reservoir_date, 0
        )
        self._use_heuristic = check_if_none(hydro_properties.use_heuristic, True)
        self._power_to_level = check_if_none(hydro_properties.power_to_level, False)
        self._use_leeway = check_if_none(hydro_properties.use_leeway, False)
        self._leeway_low = check_if_none(hydro_properties.leeway_low, 1)
        self._leeway_up = check_if_none(hydro_properties.leeway_up, 1)
        self._pumping_efficiency = check_if_none(hydro_properties.pumping_efficiency, 1)

    @computed_field  # type: ignore[misc]
    @property
    def hydro_ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            "inter-daily-breakdown": {
                f"{self._area_id}": f"{self._inter_daily_breakdown:.6f}"
            },
            "intra-daily-modulation": {
                f"{self._area_id}": f"{self._intra_daily_modulation:.6f}"
            },
            "inter-monthly-breakdown": {
                f"{self._area_id}": f"{self._inter_monthly_breakdown:.6f}"
            },
            "reservoir": {f"{self._area_id}": f"{self._reservoir}".lower()},
            "reservoir capacity": {
                f"{self._area_id}": f"{self._reservoir_capacity:.6f}"
            },
            "follow load": {f"{self._area_id}": f"{self._follow_load}".lower()},
            "use water": {f"{self._area_id}": f"{self._use_water}".lower()},
            "hard bounds": {f"{self._area_id}": f"{self._hard_bounds}".lower()},
            "initialize reservoir date": {
                f"{self._area_id}": f"{self._initialize_reservoir_date}"
            },
            "use heuristic": {f"{self._area_id}": f"{self._use_heuristic}".lower()},
            "power to level": {f"{self._area_id}": f"{self._power_to_level}".lower()},
            "use leeway": {f"{self._area_id}": f"{self._use_leeway}".lower()},
            "leeway low": {f"{self._area_id}": f"{self._leeway_low:.6f}"},
            "leeway up": {f"{self._area_id}": f"{self._leeway_up:.6f}"},
            "pumping efficiency": {
                f"{self._area_id}": f"{self._pumping_efficiency:.6f}"
            },
        }

    def yield_hydro_properties(self) -> HydroProperties:
        return HydroProperties(
            inter_daily_breakdown=self._inter_daily_breakdown,
            intra_daily_modulation=self._intra_daily_modulation,
            inter_monthly_breakdown=self._inter_monthly_breakdown,
            reservoir=self._reservoir,
            reservoir_capacity=self._reservoir_capacity,
            follow_load=self._follow_load,
            use_water=self._use_water,
            hard_bounds=self._hard_bounds,
            initialize_reservoir_date=self._initialize_reservoir_date,
            use_heuristic=self._use_heuristic,
            power_to_level=self._power_to_level,
            use_leeway=self._use_leeway,
            leeway_low=self._leeway_low,
            leeway_up=self._leeway_up,
            pumping_efficiency=self._pumping_efficiency,
        )


class Hydro:
    def __init__(  # type: ignore #
        self,
        service,
        area_id: str,
        properties: Optional[HydroProperties] = None,
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]] = None,
    ):
        self._area_id = area_id
        self._service = service
        self._properties = properties
        self._matrices = matrices

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def properties(self) -> Optional[HydroProperties]:
        return self._properties

    @property
    def matrices(self) -> Optional[Dict[HydroMatrixName, pd.DataFrame]]:
        return self._matrices
