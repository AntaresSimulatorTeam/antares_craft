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

import os

from pathlib import Path
from typing import Any, List, Optional

import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesLocal
from antares.service.base_services import BaseRenewableService
from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.matrix_tool import df_read
from antares.tools.time_series_tool import TimeSeriesFileType


class RenewableLocalService(BaseRenewableService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_renewable_properties(
        self, renewable_cluster: RenewableCluster, properties: RenewableClusterProperties
    ) -> RenewableClusterProperties:
        raise NotImplementedError
    
    def _read_timeseries(self, ts_file_type: TimeSeriesFileType, study_path: Path, area_id: Optional[str] = None, renewable_id: Optional[str] = None) -> pd.DataFrame:
        file_path = study_path / (
            ts_file_type.value
            if not (area_id or renewable_id)
            else ts_file_type.value.format(area_id=area_id, renewable_id=renewable_id)
        )
        if os.path.getsize(file_path) != 0:
            _time_series = df_read(file_path)
        else:
            _time_series = pd.DataFrame()

        return _time_series

    def get_renewable_matrix(
        self,
        renewable: RenewableCluster,
    ) -> pd.DataFrame:
        return self._read_timeseries(TimeSeriesFileType.RENEWABLE_DATA_SERIES, self.config.study_path, area_id=renewable.area_id, renewable_id=renewable.id)


    def read_renewables(self, area_id: str) -> List[RenewableCluster]:
        renewable_dict = IniFile(self.config.study_path, IniFileTypes.RENEWABLES_LIST_INI, area_name=area_id).ini_dict
        renewables_clusters = []
        if renewable_dict:
            for renewable_cluster in renewable_dict:
                renewable_properties = RenewableClusterPropertiesLocal(
                    group=renewable_dict[renewable_cluster]["group"],
                    renewable_name=renewable_dict[renewable_cluster]["name"],
                    enabled=renewable_dict[renewable_cluster]["enabled"],
                    unit_count=renewable_dict[renewable_cluster]["unitcount"],
                    nominal_capacity=renewable_dict[renewable_cluster]["nominalcapacity"],
                    ts_interpretation=renewable_dict[renewable_cluster]["ts-interpretation"],
                )
                renewables_clusters.append(RenewableCluster(renewable_service=self, area_id=area_id, name=renewable_dict[renewable_cluster]["name"], properties=renewable_properties.yield_renewable_cluster_properties()))
        return renewables_clusters
    