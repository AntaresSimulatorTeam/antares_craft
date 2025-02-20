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

from typing import Any

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseThermalService
from antares.craft.service.local_services.models.thermal import ThermalClusterPropertiesLocal
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class ThermalLocalService(BaseThermalService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterPropertiesUpdate
    ) -> ThermalClusterProperties:
        raise NotImplementedError

    @override
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
            cluster_id=thermal_cluster.id,
        )

    @override
    def read_thermal_clusters(self, area_id: str) -> list[ThermalCluster]:
        thermal_dict = IniFile(
            self.config.study_path, InitializationFilesTypes.THERMAL_LIST_INI, area_id=area_id
        ).ini_dict
        if not thermal_dict:
            return []

        return [
            ThermalCluster(
                thermal_service=self,
                area_id=area_id,
                name=thermal_data["name"],
                properties=ThermalClusterPropertiesLocal.model_validate(thermal_data).to_user_model(),
            )
            for thermal_data in thermal_dict.values()
        ]

    @override
    def update_thermal_matrix(
        self, thermal_cluster: ThermalCluster, matrix: pd.DataFrame, ts_name: ThermalClusterMatrixName
    ) -> None:
        raise NotImplementedError
