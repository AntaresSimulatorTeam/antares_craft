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
    """Law options used for series generation.
    The uniform law is used by default.
    """

    UNIFORM = "uniform"
    GEOMETRIC = "geometric"


class ThermalClusterGroup(EnumIgnoreCase):
    """Enumeration of the different possibilities of thermal cluster group.

    Attributes:
        NUCLEAR: Nuclear.
        LIGNITE: Lignite.
        HARD_COAL: Hard coal.
        GAS: Gas.
        OIL: Oil.
        MIXED_FUEL: Mixed fuel.
        OTHER1: Other 1.
        OTHER2: Other 2.
        OTHER3: Other 3.
        OTHER4: Other 4.
    """

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
        if isinstance(value, str):
            # Check if any group value matches the input value ignoring case sensitivity.
            if any(value.upper() == group.value.upper() for group in cls):
                return cast(ThermalClusterGroup, super()._missing_(value))
            # If a group is not found, return the default group ('OTHER1' by default).
            # Note that 'OTHER' is an alias for 'OTHER1'.
            return cls.OTHER1
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
    """Thermal cluster properties.

    Attributes:
        group: Type of thermal generation to organize clusters.
        gen_ts:
        min_stable_power:
        min_up_time: Duration needed for the cluster to reach its nominal capacity
            from an initial off state.
        min_down_time: Duration needed for the cluster to shutdown from its nominal capacity.
        must_run: Whether the cluster must run or not.
        spinning:
        volatility_forced:
        volatility_planned:
        law_forced:
        law_planned:
        marginal_cost: Marginal cost.
        spread_cost: Spread cost.
        fixed_cost:
        startup_cost: Start up cost of a unit.
        market_bid_cost: Market bid cost.
        co2: Emission rate of $\\ce{CO2}$ in t/MWh.
        nh3: Emission rate of $\\ce{NH3}$ in t/MWh.
        so2: Emission rate of $\\ce{SO2}$ in t/MWh.
        nox: Emission rate of $\\ce{NOx}$ in t/MWh.
        pm2_5: Emission rate of $\\ce{PM_{2.5}}$ in t/MWh.
        pm5: Emission rate of $\\ce{PM5}$ in t/MWh.
        pm10: Emission rate of $\\ce{PM10}$ in t/MWh.
        nmvoc: Emission rate of $\\ce{NMVOC}$ in t/MWh.
        op1: Emission rate of other polluant 1 in t/MWh.
        op2: Emission rate of other polluant 2 in t/MWh.
        op3: Emission rate of other polluant 3 in t/MWh.
        op4: Emission rate of other polluant 4 in t/MWh.
        op5: Emission rate of other polluant 5 in t/MWh.
        cost_generation: Generation cost.
        efficiency: Efficiency of the cluster.
        variable_o_m_cost: Variable O&M costs.
    """

    group: str = ThermalClusterGroup.OTHER1.value
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
    """Update thermal cluster properties.

    Attributes:
        group: Type of thermal generation to organize clusters.
        gen_ts:
        min_stable_power:
        min_up_time: Duration needed for the cluster to reach its nominal capacity
            from an initial off state.
        min_down_time: Duration needed for the cluster to shutdown from its nominal capacity.
        must_run: Whether the cluster must run or not.
        spinning:
        volatility_forced:
        volatility_planned:
        law_forced:
        law_planned:
        marginal_cost: Marginal cost.
        spread_cost: Spread cost.
        fixed_cost:
        startup_cost: Start up cost of a unit.
        market_bid_cost: Market bid cost.
        co2: Emission rate of $\\ce{CO2}$ in t/MWh.
        nh3: Emission rate of $\\ce{NH3}$ in t/MWh.
        so2: Emission rate of $\\ce{SO2}$ in t/MWh.
        nox: Emission rate of $\\ce{NOx}$ in t/MWh.
        pm2_5: Emission rate of $\\ce{PM{2.5}}$ in t/MWh.
        pm5: Emission rate of $\\ce{PM5}$ in t/MWh.
        pm10: Emission rate of $\\ce{PM10}$ in t/MWh.
        nmvoc: Emission rate of $\\ce{NMVOC}$ in t/MWh.
        op1: Emission rate of other polluant 1 in t/MWh.
        op2: Emission rate of other polluant 2 in t/MWh.
        op3: Emission rate of other polluant 3 in t/MWh.
        op4: Emission rate of other polluant 4 in t/MWh.
        op5: Emission rate of other polluant 5 in t/MWh.
        cost_generation: Generation cost.
        efficiency: Efficiency of the cluster.
        variable_o_m_cost: Variable O&M costs.
    """

    group: Optional[str] = None
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
    """
    TODO check if it's okay

    Attributes:
        PREPRO_DATA: Hourly availability data generation.
        PREPRO_MODULATION: Hourly modulation of the marginal cost, the market bid,
            the capacity modulation and the minimal generation.
        SERIES: Daily time-series of FO duration, PO duration, FO rate, PO rate,
            NPO min and NPO max necessary for time-series generation.
        SERIES_CO2_COST: Hourly CO2 cost time-series.
        SERIES_FUEL_COST: Hourly fuel cost time-series.
    """

    PREPRO_DATA = "data"
    PREPRO_MODULATION = "modulation"
    SERIES = "series"
    SERIES_CO2_COST = "CO2Cost"
    SERIES_FUEL_COST = "fuelCost"


class ThermalCluster:
    """Thermal cluster modelling object"""

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
        """Area ID."""
        return self._area_id

    @property
    def name(self) -> str:
        """Name of the thermal cluster."""
        return self._name

    @property
    def id(self) -> str:
        """ID of the thermal cluster."""
        return self._id

    @property
    def properties(self) -> ThermalClusterProperties:
        """Properties of the thermal cluster."""
        return self._properties

    def update_properties(self, properties: ThermalClusterPropertiesUpdate) -> ThermalClusterProperties:
        """Update properties of the thermal cluster.

        Args:
            properties: Properties to update.
        """
        new_properties = self._thermal_service.update_thermal_clusters_properties({self: properties})
        self._properties = new_properties[self]
        return self._properties

    def get_prepro_data_matrix(self) -> pd.DataFrame:
        """TODO"""
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.PREPRO_DATA)

    def get_prepro_modulation_matrix(self) -> pd.DataFrame:
        """TODO"""
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.PREPRO_MODULATION)

    def get_series_matrix(self) -> pd.DataFrame:
        """TODO"""
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES)

    def get_co2_cost_matrix(self) -> pd.DataFrame:
        """Get $\\ce{CO2}$ cost matrix.

        Returns:
            The $\\ce{CO2}$ cost matrix.
        """
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES_CO2_COST)

    def get_fuel_cost_matrix(self) -> pd.DataFrame:
        """Get fuel cost matrix.

        Returns:
            The fuel cost matrix.
        """
        return self._thermal_service.get_thermal_matrix(self, ThermalClusterMatrixName.SERIES_FUEL_COST)

    def set_prepro_data(self, matrix: pd.DataFrame) -> None:
        """TODO: what is prepo? didn't see in the UI.

        Args:
            matrix:
        """
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.PREPRO_DATA)

    def set_prepro_modulation(self, matrix: pd.DataFrame) -> None:
        """TODO

        Args:
            matrix:
        """
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.PREPRO_MODULATION)

    def set_series(self, matrix: pd.DataFrame) -> None:
        """Set TODO

        Args:
            matrix:
        """
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES)

    def set_co2_cost(self, matrix: pd.DataFrame) -> None:
        """Set $\\ce{CO2}$ cost matrix.

        Args:
            matrix: The $\\ce{CO2}$ cost matrix.
        """
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES_CO2_COST)

    def set_fuel_cost(self, matrix: pd.DataFrame) -> None:
        """Set fuel cost matrix.

        Args:
            matrix: The fuel cost matrix.
        """
        self._thermal_service.set_thermal_matrix(self, matrix, ThermalClusterMatrixName.SERIES_FUEL_COST)
