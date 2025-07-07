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
from antares.craft.exceptions.exceptions import RenewablePropertiesUpdateError
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.service.local_services.models.renewable import RenewableClusterPropertiesLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class RenewableLocalService(BaseRenewableService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def _get_ini_path(self, area_id: str) -> Path:
        return self.config.study_path / "input" / "renewables" / "clusters" / area_id / "list.ini"

    def read_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_ini_path(area_id))

    def save_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self._get_ini_path(area_id))

    @override
    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.RENEWABLE_SERIES, self.config.study_path, area_id=area_id, cluster_id=cluster_id
        )

    @override
    def read_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        renewables: dict[str, dict[str, RenewableCluster]] = {}
        cluster_path = self.config.study_path / "input" / "renewables" / "clusters"
        if not cluster_path.exists():
            return {}
        for folder in cluster_path.iterdir():
            if folder.is_dir():
                area_id = folder.name

                renewable_dict = self.read_ini(area_id)

                for renewable_data in renewable_dict.values():
                    renewable_cluster = RenewableCluster(
                        renewable_service=self,
                        area_id=area_id,
                        name=renewable_data["name"],
                        properties=RenewableClusterPropertiesLocal.model_validate(renewable_data).to_user_model(),
                    )

                    renewables.setdefault(area_id, {})[renewable_cluster.id] = renewable_cluster

        return renewables

    @override
    def set_series(self, renewable_cluster: RenewableCluster, matrix: pd.DataFrame) -> None:
        checks_matrix_dimensions(matrix, f"renewable/{renewable_cluster.area_id}/{renewable_cluster.id}", "series")
        write_timeseries(
            self.config.study_path,
            matrix,
            TimeSeriesFileType.RENEWABLE_SERIES,
            renewable_cluster.area_id,
            renewable_cluster.id,
        )

    @override
    def update_renewable_clusters_properties(
        self, new_props: dict[RenewableCluster, RenewableClusterPropertiesUpdate]
    ) -> dict[RenewableCluster, RenewableClusterProperties]:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        new_properties_dict: dict[RenewableCluster, RenewableClusterProperties] = {}
        cluster_name_to_object: dict[str, RenewableCluster] = {}

        properties_by_areas: dict[str, dict[str, RenewableClusterPropertiesUpdate]] = {}

        for renewable_cluster, properties in new_props.items():
            properties_by_areas.setdefault(renewable_cluster.area_id, {})[renewable_cluster.name] = properties
            cluster_name_to_object[renewable_cluster.name] = renewable_cluster

        for area_id, value in properties_by_areas.items():
            all_renewable_names = set(value.keys())  # used to raise an Exception if a cluster doesn't exist
            renewable_dict = self.read_ini(area_id)
            for renewable in renewable_dict.values():
                renewable_name = renewable["name"]
                if renewable_name in value:
                    all_renewable_names.remove(renewable_name)

                    # Update properties
                    upd_properties = RenewableClusterPropertiesLocal.from_user_model(value[renewable_name])
                    upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_unset=True)
                    renewable.update(upd_props_as_dict)

                    # Prepare the object to return
                    local_dict = copy.deepcopy(renewable)
                    del local_dict["name"]
                    local_properties = RenewableClusterPropertiesLocal.model_validate(local_dict)
                    new_properties_dict[cluster_name_to_object[renewable_name]] = local_properties.to_user_model()

            if len(all_renewable_names) > 0:
                raise RenewablePropertiesUpdateError(
                    next(iter(all_renewable_names)), area_id, "The cluster does not exist"
                )

            memory_mapping[area_id] = renewable_dict

        # Update ini files
        for area_id, ini_content in memory_mapping.items():
            self.save_ini(ini_content, area_id)

        return new_properties_dict
