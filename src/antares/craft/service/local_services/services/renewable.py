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
from antares.craft.exceptions.exceptions import RenewablePropertiesUpdateError
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.service.local_services.models.renewable import RenewableClusterPropertiesLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class RenewableLocalService(BaseRenewableService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_renewable_properties(
        self, renewable_cluster: RenewableCluster, properties: RenewableClusterPropertiesUpdate
    ) -> RenewableClusterProperties:
        area_id = renewable_cluster.area_id
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.RENEWABLES_LIST_INI, area_id=area_id)
        renewable_dict = ini_file.ini_dict
        for renewable in renewable_dict.values():
            if renewable["name"] == renewable_cluster.name:
                # Update properties
                upd_properties = RenewableClusterPropertiesLocal.from_user_model(properties)
                upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                renewable.update(upd_props_as_dict)

                # Update ini file
                ini_file.ini_dict = renewable_dict
                ini_file.write_ini_file()

                # Prepare the object to return
                local_dict = copy.deepcopy(renewable)
                del local_dict["name"]
                local_properties = RenewableClusterPropertiesLocal.model_validate(local_dict)

                return local_properties.to_user_model()
        raise RenewablePropertiesUpdateError(renewable_cluster.name, area_id, "The cluster does not exist")

    @override
    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.RENEWABLE_SERIES, self.config.study_path, area_id=area_id, cluster_id=cluster_id
        )

    @override
    def read_renewables(self, area_id: str) -> list[RenewableCluster]:
        renewable_dict = IniFile(
            self.config.study_path, InitializationFilesTypes.RENEWABLES_LIST_INI, area_id=area_id
        ).ini_dict

        if not renewable_dict:
            return []

        return [
            RenewableCluster(
                renewable_service=self,
                area_id=area_id,
                name=renewable_data["name"],
                properties=RenewableClusterPropertiesLocal.model_validate(renewable_data).to_user_model(),
            )
            for renewable_data in renewable_dict.values()
        ]

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
