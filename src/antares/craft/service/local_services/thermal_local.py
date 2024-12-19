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

from typing import Any, List

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterProperties,
    ThermalClusterPropertiesLocal,
)
from antares.craft.service.base_services import BaseThermalService
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class ThermalLocalService(BaseThermalService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterProperties
    ) -> ThermalClusterProperties:
        raise NotImplementedError

    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        if ts_name.value == "series":
            time_serie_type = TimeSeriesFileType.THERMAL_SERIES
        elif ts_name.value == "modulation":
            time_serie_type = TimeSeriesFileType.THERMAL_MODULATION
        elif ts_name.value == "data":
            time_serie_type = TimeSeriesFileType.THERMAL_DATA
        elif ts_name.value == "CO2Cost":
            time_serie_type = TimeSeriesFileType.THERMAL_CO2
        else:
            time_serie_type = TimeSeriesFileType.THERMAL_FUEL

        return read_timeseries(
            time_serie_type,
            self.config.study_path,
            area_id=thermal_cluster.area_id,
            cluster_id=thermal_cluster.properties.group.value,
        )

    def read_thermal_clusters(self, area_id: str) -> List[ThermalCluster]:
        thermal_dict = IniFile(self.config.study_path, IniFileTypes.THERMAL_LIST_INI, area_id=area_id).ini_dict
        thermal_clusters = []
        if thermal_dict:
            for thermal_cluster in thermal_dict:
                # TODO refactor this as it is really not clean
                thermal_properties = ThermalClusterPropertiesLocal(
                    group=thermal_dict[thermal_cluster].get("group"),
                    thermal_name=thermal_dict[thermal_cluster]["name"],
                    enabled=thermal_dict[thermal_cluster].get("enabled"),
                    unit_count=thermal_dict[thermal_cluster].get("unitcount"),
                    nominal_capacity=thermal_dict[thermal_cluster].get("nominalcapacity"),
                    gen_ts=thermal_dict[thermal_cluster].get("gen-ts"),
                    min_stable_power=thermal_dict[thermal_cluster].get("min-stable-power"),
                    min_up_time=thermal_dict[thermal_cluster].get("min-up-time"),
                    min_down_time=thermal_dict[thermal_cluster].get("min-down-time"),
                    must_run=thermal_dict[thermal_cluster].get("must-run"),
                    spinning=thermal_dict[thermal_cluster].get("spinning"),
                    volatility_forced=thermal_dict[thermal_cluster].get("volatility.forced"),
                    volatility_planned=thermal_dict[thermal_cluster].get("volatility.planned"),
                    law_forced=thermal_dict[thermal_cluster].get("law.forced"),
                    law_planned=thermal_dict[thermal_cluster].get("law.planned"),
                    marginal_cost=thermal_dict[thermal_cluster].get("marginal-cost"),
                    spread_cost=thermal_dict[thermal_cluster].get("spread-cost"),
                    fixed_cost=thermal_dict[thermal_cluster].get("fixed-cost"),
                    startup_cost=thermal_dict[thermal_cluster].get("startup-cost"),
                    market_bid_cost=thermal_dict[thermal_cluster].get("market-bid-cost"),
                    co2=thermal_dict[thermal_cluster].get("co2"),
                    nh3=thermal_dict[thermal_cluster].get("nh3"),
                    so2=thermal_dict[thermal_cluster].get("so2"),
                    nox=thermal_dict[thermal_cluster].get("nox"),
                    pm2_5=thermal_dict[thermal_cluster].get("pm2_5"),
                    pm5=thermal_dict[thermal_cluster].get("pm5"),
                    pm10=thermal_dict[thermal_cluster].get("pm10"),
                    nmvoc=thermal_dict[thermal_cluster].get("nmvoc"),
                    op1=thermal_dict[thermal_cluster].get("op1"),
                    op2=thermal_dict[thermal_cluster].get("op2"),
                    op3=thermal_dict[thermal_cluster].get("op3"),
                    op4=thermal_dict[thermal_cluster].get("op4"),
                    op5=thermal_dict[thermal_cluster].get("op5"),
                    cost_generation=thermal_dict[thermal_cluster].get("costgeneration"),
                    efficiency=thermal_dict[thermal_cluster].get("efficiency"),
                    variable_o_m_cost=thermal_dict[thermal_cluster].get("variableomcost"),
                )

                thermal_clusters.append(
                    ThermalCluster(
                        thermal_service=self,
                        area_id=area_id,
                        name=thermal_dict[thermal_cluster]["name"],
                        properties=thermal_properties.yield_thermal_cluster_properties(),
                    )
                )
        return thermal_clusters
