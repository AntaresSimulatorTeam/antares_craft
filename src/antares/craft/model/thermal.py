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
from typing import Optional, cast

import pandas as pd

from typing_extensions import override

from antares.craft.model.cluster import ClusterProperties, ClusterPropertiesUpdate
from antares.craft.service.base_services import BaseThermalService
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id


class LawOption(Enum):
    """
    Law options used for series generation.
    The UNIFORM `law` is used by default.
    """

    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class ThermalClusterGroup(EnumIgnoreCase):
    NUCLEAR = "nuclear"
    LIGNITE = "lignite"
    HARD_COAL = "hard coal"
    GAS = "gas"
    OIL = "oil"
    MIXED_FUEL = "mixed fuel"
    OTHER1 = "other 1"
    OTHER2 = "other 2"
    OTHER3 = "other 3"
    OTHER4 = "other 4"

    @classmethod
    @override
    def _missing_(cls, value: object) -> Optional["ThermalClusterGroup"]:
        if isinstance(value, str) and value.upper() == "OTHER":
            return ThermalClusterGroup.OTHER1
        return cast(Optional["ThermalClusterGroup"], super()._missing_(value))


class LocalTSGenerationBehavior(Enum):
    """
    Options related to time series generation.
    The option `USE_GLOBAL` is used by default.

    Attributes:
        USE_GLOBAL: Use the global time series parameters.
        FORCE_NO_GENERATION: Do not generate time series.
        FORCE_GENERATION: Force the generation of time series.
    """

    USE_GLOBAL = "use global"
    FORCE_NO_GENERATION = "force no generation"
    FORCE_GENERATION = "force generation"


class ThermalCostGeneration(Enum):
    SET_MANUALLY = "SetManually"
    USE_COST_TIME_SERIES = "useCostTimeseries"


@dataclass(frozen=True)
class ThermalClusterProperties(ClusterProperties):
    group: ThermalClusterGroup = ThermalClusterGroup.OTHER1
    gen_ts: LocalTSGenerationBehavior = LocalTSGenerationBehavior.USE_GLOBAL
    min_stable_power: float = 0
    min_up_time: int = 1
    min_down_time: int = 1
    must_run: bool = False
    spinning: float = 0
    volatility_forced: float = 0
    volatility_planned: float = 0
    law_forced: LawOption = LawOption.UNIFORM
    law_planned: LawOption = LawOption.UNIFORM
    marginal_cost: float = 0
    spread_cost: float = 0
    fixed_cost: float = 0
    startup_cost: float = 0
    market_bid_cost: float = 0
    co2: float = 0
    nh3: float = 0
    so2: float = 0
    nox: float = 0
    pm2_5: float = 0
    pm5: float = 0
    pm10: float = 0
    nmvoc: float = 0
    op1: float = 0
    op2: float = 0
    op3: float = 0
    op4: float = 0
    op5: float = 0
    cost_generation: ThermalCostGeneration = ThermalCostGeneration.SET_MANUALLY
    efficiency: float = 100
    variable_o_m_cost: float = 0


@dataclass
class ThermalClusterPropertiesUpdate(ClusterPropertiesUpdate):
    group: Optional[ThermalClusterGroup] = None
    gen_ts: Optional[LocalTSGenerationBehavior] = None
    min_stable_power: Optional[float] = None
    min_up_time: Optional[int] = None
    min_down_time: Optional[int] = None
    must_run: Optional[bool] = None
    spinning: Optional[float] = None
    volatility_forced: Optional[float] = None
    volatility_planned: Optional[float] = None
    law_forced: Optional[LawOption] = None
    law_planned: Optional[LawOption] = None
    marginal_cost: Optional[float] = None
    spread_cost: Optional[float] = None
    fixed_cost: Optional[float] = None
    startup_cost: Optional[float] = None
    market_bid_cost: Optional[float] = None
    co2: Optional[float] = None
    nh3: Optional[float] = None
    so2: Optional[float] = None
    nox: Optional[float] = None
    pm2_5: Optional[float] = None
    pm5: Optional[float] = None
    pm10: Optional[float] = None
    nmvoc: Optional[float] = None
    op1: Optional[float] = None
    op2: Optional[float] = None
    op3: Optional[float] = None
    op4: Optional[float] = None
    op5: Optional[float] = None
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[float] = None
    variable_o_m_cost: Optional[float] = None


class ThermalClusterMatrixName(Enum):
    PREPRO_DATA = "data"
    PREPRO_MODULATION = "modulation"
    SERIES = "series"
    SERIES_CO2_COST = "CO2Cost"
    SERIES_FUEL_COST = "fuelCost"


class ThermalCluster:
    def __init__(
        self,
        thermal_service: BaseThermalService,
        area_id: str,
        name: str,
        properties: Optional[ThermalClusterProperties] = None,
    ):
        self._area_id = area_id
        self._thermal_service: BaseThermalService = thermal_service
        self._name = name
        self._id = transform_name_to_id(name)
        self._properties = properties or ThermalClusterProperties()

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def properties(self) -> ThermalClusterProperties:
        return self._properties

    def update_properties(self, properties: ThermalClusterPropertiesUpdate) -> ThermalClusterProperties:
        new_properties = self._thermal_service.update_thermal_clusters_properties({self: properties})
        self._properties = new_properties[self]
        return self._properties

    def get_prepro_data_matrix(self) -> pd.DataFrame:
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.PREPRO_DATA)

    def get_prepro_modulation_matrix(self) -> pd.DataFrame:
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.PREPRO_MODULATION)

    def get_series_matrix(self) -> pd.DataFrame:
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES)

    def get_co2_cost_matrix(self) -> pd.DataFrame:
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES_CO2_COST)

    def get_fuel_cost_matrix(self) -> pd.DataFrame:
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES_FUEL_COST)

    def set_prepro_data(self, matrix: pd.DataFrame) -> None:
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.PREPRO_DATA)

    def set_prepro_modulation(self, matrix: pd.DataFrame) -> None:
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.PREPRO_MODULATION)

    def set_series(self, matrix: pd.DataFrame) -> None:
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES)

    def set_co2_cost(self, matrix: pd.DataFrame) -> None:
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES_CO2_COST)

    def set_fuel_cost(self, matrix: pd.DataFrame) -> None:
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES_FUEL_COST)
