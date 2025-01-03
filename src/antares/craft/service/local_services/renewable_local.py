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
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesLocal
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
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

    def read_renewables(self, area_id: str) -> List[RenewableCluster]:
        renewable_dict = IniFile(self.config.study_path, IniFileTypes.RENEWABLES_LIST_INI, area_id=area_id).ini_dict
        renewables_clusters = []
        if renewable_dict:
            for renewable_cluster in renewable_dict:
                renewable_properties = RenewableClusterPropertiesLocal(
                    group=renewable_dict[renewable_cluster].get("group"),
                    renewable_name=renewable_dict[renewable_cluster].get("name"),
                    enabled=renewable_dict[renewable_cluster].get("enabled"),
                    unit_count=renewable_dict[renewable_cluster].get("unitcount"),
                    nominal_capacity=renewable_dict[renewable_cluster].get("nominalcapacity"),
                    ts_interpretation=renewable_dict[renewable_cluster].get("ts-interpretation"),
                )
                renewables_clusters.append(
                    RenewableCluster(
                        renewable_service=self,
                        area_id=area_id,
                        name=renewable_dict[renewable_cluster]["name"],
                        properties=renewable_properties.yield_renewable_cluster_properties(),
                    )
                )
        return renewables_clusters
