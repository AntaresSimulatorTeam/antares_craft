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

from pathlib import Path
from typing import Any

import pandas as pd

from typing_extensions import override

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
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType

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

    def _get_ini_path(self, area_id: str) -> Path:
        return self.config.study_path / "input" / "thermal" / "clusters" / area_id / "list.ini"

    def read_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_ini_path(area_id))

    def save_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self._get_ini_path(area_id))

    @override
    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        return read_timeseries(
            MAPPING[ts_name],
            self.config.study_path,
            area_id=thermal_cluster.area_id,
            cluster_id=thermal_cluster.id,
        )

    @override
    def read_thermal_clusters(self) -> dict[str, dict[str, ThermalCluster]]:
        thermals: dict[str, dict[str, ThermalCluster]] = {}
        cluster_path = self.config.study_path / "input" / "thermal" / "clusters"
        if not cluster_path.exists():
            return {}
        for folder in cluster_path.iterdir():
            if folder.is_dir():
                area_id = folder.name
                thermal_dict = self.read_ini(area_id)

                for thermal_data in thermal_dict.values():
                    thermal_cluster = ThermalCluster(
                        thermal_service=self,
                        area_id=area_id,
                        name=thermal_data["name"],
                        properties=ThermalClusterPropertiesLocal.model_validate(thermal_data).to_user_model(),
                    )

                    thermals.setdefault(area_id, {})[thermal_cluster.id] = thermal_cluster

        return thermals

    @override
    def set_thermal_matrix(
        self, thermal_cluster: ThermalCluster, matrix: pd.DataFrame, ts_name: ThermalClusterMatrixName
    ) -> None:
        checks_matrix_dimensions(matrix, f"thermal/{thermal_cluster.area_id}/{thermal_cluster.id}", ts_name.value)
        write_timeseries(self.config.study_path, matrix, MAPPING[ts_name], thermal_cluster.area_id, thermal_cluster.id)

    @override
    def update_thermal_clusters_properties(
        self, new_properties: dict[ThermalCluster, ThermalClusterPropertiesUpdate]
    ) -> dict[ThermalCluster, ThermalClusterProperties]:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        new_properties_dict: dict[ThermalCluster, ThermalClusterProperties] = {}
        cluster_name_to_object: dict[str, ThermalCluster] = {}

        properties_by_areas: dict[str, dict[str, ThermalClusterPropertiesUpdate]] = {}
        for thermal_cluster, properties in new_properties.items():
            properties_by_areas.setdefault(thermal_cluster.area_id, {})[thermal_cluster.name] = properties
            cluster_name_to_object[thermal_cluster.name] = thermal_cluster

        for area_id, value in properties_by_areas.items():
            all_thermal_names = set(value.keys())  # used to raise an Exception if a cluster doesn't exist
            thermal_dict = self.read_ini(area_id)
            for thermal in thermal_dict.values():
                thermal_name = thermal["name"]
                if thermal_name in value:
                    all_thermal_names.remove(thermal_name)

                    # Update properties
                    upd_properties = ThermalClusterPropertiesLocal.from_user_model(value[thermal_name])
                    upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_unset=True)
                    thermal.update(upd_props_as_dict)

                    # Prepare the object to return
                    local_dict = copy.deepcopy(thermal)
                    del local_dict["name"]
                    local_properties = ThermalClusterPropertiesLocal.model_validate(local_dict)
                    new_properties_dict[cluster_name_to_object[thermal_name]] = local_properties.to_user_model()

            if len(all_thermal_names) > 0:
                raise ThermalPropertiesUpdateError(next(iter(all_thermal_names)), area_id, "The cluster does not exist")

            memory_mapping[area_id] = thermal_dict

        # Update ini files
        for area_id, ini_content in memory_mapping.items():
            self.save_ini(ini_content, area_id)

        return new_properties_dict
