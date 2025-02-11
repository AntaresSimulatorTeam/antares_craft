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
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
)
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.service.local_services.models.renewable import RenewableClusterPropertiesLocal
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
    def update_renewable_matrix(self, renewable_cluster: RenewableCluster, matrix: pd.DataFrame) -> None:
        raise NotImplementedError
