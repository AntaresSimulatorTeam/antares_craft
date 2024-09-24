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
from typing import Optional, Any

import pandas as pd
from pydantic import BaseModel, computed_field

from antares.model.cluster import ClusterProperties
from antares.tools.contents_tool import transform_name_to_id
from antares.tools.ini_tool import check_if_none


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


class ThermalClusterProperties(ClusterProperties):
    """
    Thermal cluster configuration model.
    This model describes the configuration parameters for a thermal cluster.
    """

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
    # version 860
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
    # version 870
    cost_generation: Optional[ThermalCostGeneration] = None
    efficiency: Optional[float] = None
    variable_o_m_cost: Optional[float] = None


class ThermalClusterPropertiesLocal(BaseModel):
    def __init__(
        self,
        thermal_name: str,
        thermal_cluster_properties: Optional[ThermalClusterProperties] = None,
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        thermal_cluster_properties = thermal_cluster_properties or ThermalClusterProperties()
        self._thermal_name = thermal_name
        self._enabled = check_if_none(thermal_cluster_properties.enabled, True)
        self._unit_count = check_if_none(thermal_cluster_properties.unit_count, 1)
        self._nominal_capacity = check_if_none(thermal_cluster_properties.nominal_capacity, 0)
        self._group = (
            # The value OTHER1 matches AntaresWeb if a cluster is created via API without providing a group
            thermal_cluster_properties.group or ThermalClusterGroup.OTHER1
        )
        self._gen_ts = check_if_none(thermal_cluster_properties.gen_ts, LocalTSGenerationBehavior.USE_GLOBAL)
        self._min_stable_power = check_if_none(thermal_cluster_properties.min_stable_power, 0)
        self._min_up_time = check_if_none(thermal_cluster_properties.min_up_time, 1)
        self._min_down_time = check_if_none(thermal_cluster_properties.min_down_time, 1)
        self._must_run = check_if_none(thermal_cluster_properties.must_run, False)
        self._spinning = check_if_none(thermal_cluster_properties.spinning, 0)
        self._volatility_forced = check_if_none(thermal_cluster_properties.volatility_forced, 0)
        self._volatility_planned = check_if_none(thermal_cluster_properties.volatility_planned, 0)
        self._law_forced = check_if_none(thermal_cluster_properties.law_forced, LawOption.UNIFORM)
        self._law_planned = check_if_none(thermal_cluster_properties.law_planned, LawOption.UNIFORM)
        self._marginal_cost = check_if_none(thermal_cluster_properties.marginal_cost, 0)
        self._spread_cost = check_if_none(thermal_cluster_properties.spread_cost, 0)
        self._fixed_cost = check_if_none(thermal_cluster_properties.fixed_cost, 0)
        self._startup_cost = check_if_none(thermal_cluster_properties.startup_cost, 0)
        self._market_bid_cost = check_if_none(thermal_cluster_properties.market_bid_cost, 0)
        self._co2 = check_if_none(thermal_cluster_properties.co2, 0)
        self._nh3 = check_if_none(thermal_cluster_properties.nh3, 0)
        self._so2 = check_if_none(thermal_cluster_properties.so2, 0)
        self._nox = check_if_none(thermal_cluster_properties.nox, 0)
        self._pm2_5 = check_if_none(thermal_cluster_properties.pm2_5, 0)
        self._pm5 = check_if_none(thermal_cluster_properties.pm5, 0)
        self._pm10 = check_if_none(thermal_cluster_properties.pm10, 0)
        self._nmvoc = check_if_none(thermal_cluster_properties.nmvoc, 0)
        self._op1 = check_if_none(thermal_cluster_properties.op1, 0)
        self._op2 = check_if_none(thermal_cluster_properties.op2, 0)
        self._op3 = check_if_none(thermal_cluster_properties.op3, 0)
        self._op4 = check_if_none(thermal_cluster_properties.op4, 0)
        self._op5 = check_if_none(thermal_cluster_properties.op5, 0)
        self._cost_generation = check_if_none(
            thermal_cluster_properties.cost_generation,
            ThermalCostGeneration.SET_MANUALLY,
        )
        self._efficiency = check_if_none(thermal_cluster_properties.efficiency, 100)
        self._variable_o_m_cost = check_if_none(thermal_cluster_properties.variable_o_m_cost, 0)

    @computed_field  # type: ignore[misc]
    @property
    def list_ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            f"{self._thermal_name}": {
                "group": self._group.value,
                "name": self._thermal_name,
                "enabled": f"{self._enabled}",
                "unitcount": f"{self._unit_count}",
                "nominalcapacity": f"{self._nominal_capacity:.6f}",
                "gen-ts": self._gen_ts.value,
                "min-stable-power": f"{self._min_stable_power:.6f}",
                "min-up-time": f"{self._min_up_time}",
                "min-down-time": f"{self._min_down_time}",
                "must-run": f"{self._must_run}",
                "spinning": f"{self._spinning:.6f}",
                "volatility.forced": f"{self._volatility_forced:.6f}",
                "volatility.planned": f"{self._volatility_planned:.6f}",
                "law.forced": self._law_forced.value,
                "law.planned": self._law_planned.value,
                "marginal-cost": f"{self._marginal_cost:.6f}",
                "spread-cost": f"{self._spread_cost:.6f}",
                "fixed-cost": f"{self._fixed_cost:.6f}",
                "startup-cost": f"{self._startup_cost:.6f}",
                "market-bid-cost": f"{self._market_bid_cost:.6f}",
                "co2": f"{self._co2:.6f}",
                "nh3": f"{self._nh3:.6f}",
                "so2": f"{self._so2:.6f}",
                "nox": f"{self._nox:.6f}",
                "pm2_5": f"{self._pm2_5:.6f}",
                "pm5": f"{self._pm5:.6f}",
                "pm10": f"{self._pm10:.6f}",
                "nmvoc": f"{self._nmvoc:.6f}",
                "op1": f"{self._op1:.6f}",
                "op2": f"{self._op2:.6f}",
                "op3": f"{self._op3:.6f}",
                "op4": f"{self._op4:.6f}",
                "op5": f"{self._op5:.6f}",
                "costgeneration": self._cost_generation.value,
                "efficiency": f"{self._efficiency:.6f}",
                "variableomcost": f"{self._variable_o_m_cost:.6f}",
            }
        }

    def yield_thermal_cluster_properties(self) -> ThermalClusterProperties:
        return ThermalClusterProperties(
            group=self._group,
            enabled=self._enabled,
            unit_count=self._unit_count,
            nominal_capacity=self._nominal_capacity,
            gen_ts=self._gen_ts,
            min_stable_power=self._min_stable_power,
            min_up_time=self._min_up_time,
            min_down_time=self._min_down_time,
            must_run=self._must_run,
            spinning=self._spinning,
            volatility_forced=self._volatility_forced,
            volatility_planned=self._volatility_planned,
            law_forced=self._law_forced,
            law_planned=self._law_planned,
            marginal_cost=self._marginal_cost,
            spread_cost=self._spread_cost,
            fixed_cost=self._fixed_cost,
            startup_cost=self._startup_cost,
            market_bid_cost=self._market_bid_cost,
            co2=self._co2,
            nh3=self._nh3,
            so2=self._so2,
            nox=self._nox,
            pm2_5=self._pm2_5,
            pm5=self._pm5,
            pm10=self._pm10,
            nmvoc=self._nmvoc,
            op1=self._op1,
            op2=self._op2,
            op3=self._op3,
            op4=self._op4,
            op5=self._op5,
            cost_generation=self._cost_generation,
            efficiency=self._efficiency,
            variable_o_m_cost=self._variable_o_m_cost,
        )


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
