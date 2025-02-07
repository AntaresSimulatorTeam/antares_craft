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


from typing import Any, get_type_hints

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesLocal
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class RenewableLocalService(BaseRenewableService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_renewable_properties(
        self, renewable_cluster: RenewableCluster, properties: RenewableClusterProperties
    ) -> RenewableClusterProperties:
        raise NotImplementedError

    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.RENEWABLE_DATA_SERIES, self.config.study_path, area_id=area_id, cluster_id=cluster_id
        )

    def _extract_renewable_properties(self, renewable_data: dict[str, Any]) -> RenewableClusterProperties:
        property_types = get_type_hints(RenewableClusterPropertiesLocal)

        parsed_data = {
            key: property_types[key](value) if value is not None else None
            for key, value in renewable_data.items()
            if key in property_types
        }

        return RenewableClusterPropertiesLocal(**parsed_data).yield_renewable_cluster_properties()

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
                properties=self._extract_renewable_properties(renewable_data),
            )
            for renewable_data in renewable_dict.values()
        ]

    def update_renewable_matrix(self, renewable_cluster: RenewableCluster, matrix: pd.DataFrame) -> None:
        raise NotImplementedError
