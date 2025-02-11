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
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterProperties,
    RenewableClusterPropertiesLocal,
    RenewableClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
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
        raise NotImplementedError

    @override
    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.RENEWABLE_DATA_SERIES, self.config.study_path, area_id=area_id, cluster_id=cluster_id
        )

    def _extract_renewable_properties(self, renewable_data: dict[str, Any]) -> RenewableClusterProperties:
        # get_type_hints will yield a dict with every local property as key and its type as the value
        property_types = get_type_hints(RenewableClusterPropertiesLocal)

        # the name key is called "name" in renewable_data but "renewable_name" in the properties, that's why we map it
        property_mapping = {"name": "renewable_name"}

        # for each property in renewable_data, we will type it according to property_types while making sure it's not None
        # because it's Optional. If it's "name" then we get its mapping from the property_mapping dict
        parsed_data = {
            property_mapping.get(property, property): property_types[property_mapping.get(property, property)](value)
            if value is not None
            else None
            for property, value in renewable_data.items()
            if property_mapping.get(property, property) in property_types
        }

        return RenewableClusterPropertiesLocal(**parsed_data).yield_renewable_cluster_properties()

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
                properties=self._extract_renewable_properties(renewable_data),
            )
            for renewable_data in renewable_dict.values()
        ]

    @override
    def update_renewable_matrix(self, renewable_cluster: RenewableCluster, matrix: pd.DataFrame) -> None:
        raise NotImplementedError
