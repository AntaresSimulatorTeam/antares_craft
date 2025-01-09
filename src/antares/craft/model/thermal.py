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
from typing import Optional

import pandas as pd

from antares.craft.model.cluster import ClusterProperties
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import transform_name_to_id


class LawOption(Enum):
    """
    Law options used for series generation.
    The UNIFORM `law` is used by default.
    """

    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class ThermalClusterGroup(Enum):
    NUCLEAR = "Nuclear"
    LIGNITE = "Lignite"
    HARD_COAL = "Hard Coal"
    GAS = "Gas"
    OIL = "Oil"
    MIXED_FUEL = "Mixed Fuel"
    OTHER1 = "Other 1"
    OTHER2 = "Other 2"
    OTHER3 = "Other 3"
    OTHER4 = "Other 4"


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


class DefaultThermalProperties(ClusterProperties):
    """
    Thermal cluster configuration model.
    This model describes the configuration parameters for a thermal cluster.
    """

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
    # version 860
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
    # version 870
    cost_generation: ThermalCostGeneration = ThermalCostGeneration.SET_MANUALLY
    efficiency: float = 100
    variable_o_m_cost: float = 0


@all_optional_model
class ThermalClusterProperties(DefaultThermalProperties):
    pass


class ThermalClusterPropertiesLocal(DefaultThermalProperties):
    thermal_name: str

    @property
    def list_ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            f"{self.thermal_name}": {
                "group": self.group.value,
                "name": self.thermal_name,
                "enabled": f"{self.enabled}",
                "unitcount": f"{self.unit_count}",
                "nominalcapacity": f"{self.nominal_capacity:.6f}",
                "gen-ts": self.gen_ts.value,
                "min-stable-power": f"{self.min_stable_power:.6f}",
                "min-up-time": f"{self.min_up_time}",
                "min-down-time": f"{self.min_down_time}",
                "must-run": f"{self.must_run}",
                "spinning": f"{self.spinning:.6f}",
                "volatility.forced": f"{self.volatility_forced:.6f}",
                "volatility.planned": f"{self.volatility_planned:.6f}",
                "law.forced": self.law_forced.value,
                "law.planned": self.law_planned.value,
                "marginal-cost": f"{self.marginal_cost:.6f}",
                "spread-cost": f"{self.spread_cost:.6f}",
                "fixed-cost": f"{self.fixed_cost:.6f}",
                "startup-cost": f"{self.startup_cost:.6f}",
                "market-bid-cost": f"{self.market_bid_cost:.6f}",
                "co2": f"{self.co2:.6f}",
                "nh3": f"{self.nh3:.6f}",
                "so2": f"{self.so2:.6f}",
                "nox": f"{self.nox:.6f}",
                "pm2_5": f"{self.pm2_5:.6f}",
                "pm5": f"{self.pm5:.6f}",
                "pm10": f"{self.pm10:.6f}",
                "nmvoc": f"{self.nmvoc:.6f}",
                "op1": f"{self.op1:.6f}",
                "op2": f"{self.op2:.6f}",
                "op3": f"{self.op3:.6f}",
                "op4": f"{self.op4:.6f}",
                "op5": f"{self.op5:.6f}",
                "costgeneration": self.cost_generation.value,
                "efficiency": f"{self.efficiency:.6f}",
                "variableomcost": f"{self.variable_o_m_cost:.6f}",
            }
        }

    def yield_thermal_cluster_properties(self) -> ThermalClusterProperties:
        excludes = {"thermal_name", "list_ini_fields"}
        return ThermalClusterProperties.model_validate(self.model_dump(mode="json", exclude=excludes))


class ThermalClusterMatrixName(Enum):
    PREPRO_DATA = "data"
    PREPRO_MODULATION = "modulation"
    SERIES = "series"
    SERIES_CO2_COST = "CO2Cost"
    SERIES_FUEL_COST = "fuelCost"


class ThermalCluster:
    def __init__(self, thermal_service, area_id: str, name: str, properties: Optional[ThermalClusterProperties] = None):  # type: ignore # TODO: Find a way to avoid circular imports
        self._area_id = area_id
        self._thermal_service = thermal_service
        self._name = name
        self._id = transform_name_to_id(name)
        self._properties = properties or ThermalClusterProperties()

    # TODO: Add matrices.

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

    def update_properties(self, properties: ThermalClusterProperties) -> None:
        new_properties = self._thermal_service.update_thermal_properties(self, properties)
        self._properties = new_properties

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
