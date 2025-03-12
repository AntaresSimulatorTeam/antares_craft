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
import copy

from typing import Any

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import ThermalPropertiesUpdateError
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseThermalService
from antares.craft.service.local_services.models.thermal import ThermalClusterPropertiesLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override

MAPPING = {
    ThermalClusterMatrixName.PREPRO_DATA: TimeSeriesFileType.THERMAL_DATA,
    ThermalClusterMatrixName.PREPRO_MODULATION: TimeSeriesFileType.THERMAL_MODULATION,
    ThermalClusterMatrixName.SERIES: TimeSeriesFileType.THERMAL_SERIES,
    ThermalClusterMatrixName.SERIES_CO2_COST: TimeSeriesFileType.THERMAL_CO2,
    ThermalClusterMatrixName.SERIES_FUEL_COST: TimeSeriesFileType.THERMAL_FUEL,
}


class ThermalLocalService(BaseThermalService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterPropertiesUpdate
    ) -> ThermalClusterProperties:
        area_id = thermal_cluster.area_id
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_LIST_INI, area_id=area_id)
        thermal_dict = ini_file.ini_dict
        for thermal in thermal_dict.values():
            if thermal["name"] == thermal_cluster.name:
                # Update properties
                upd_properties = ThermalClusterPropertiesLocal.from_user_model(properties)
                upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                thermal.update(upd_props_as_dict)

                # Update ini file
                ini_file.ini_dict = thermal_dict
                ini_file.write_ini_file()

                # Prepare the object to return
                local_dict = copy.deepcopy(thermal)
                del local_dict["name"]
                local_properties = ThermalClusterPropertiesLocal.model_validate(local_dict)

                return local_properties.to_user_model()
        raise ThermalPropertiesUpdateError(thermal_cluster.name, area_id, "The cluster does not exist")

    @override
    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        return read_timeseries(
            MAPPING[ts_name],
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
    def set_thermal_matrix(
        self, thermal_cluster: ThermalCluster, matrix: pd.DataFrame, ts_name: ThermalClusterMatrixName
    ) -> None:
        checks_matrix_dimensions(matrix, f"thermal/{thermal_cluster.area_id}/{thermal_cluster.id}", ts_name.value)
        write_timeseries(self.config.study_path, matrix, MAPPING[ts_name], thermal_cluster.area_id, thermal_cluster.id)

    @override
    def update_multiple_thermal_clusters(
        self, new_properties: dict[ThermalCluster, ThermalClusterPropertiesUpdate]
    ) -> dict[ThermalCluster, ThermalClusterProperties]:
        new_properties_dict = {}
        for cluster, update_properties in new_properties.items():
            updated_properties = self.update_thermal_properties(cluster, update_properties)
            new_properties_dict[cluster] = updated_properties
        return new_properties_dict
