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
from antares.craft.model.st_storage import (
    STStorage,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.base_services import BaseShortTermStorageService
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.service.local_services.models.st_storage import STStoragePropertiesLocal
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStoragePropertiesUpdate
    ) -> STStorageProperties:
        raise NotImplementedError

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        if ts_name.value == "inflows":
            time_serie_type = TimeSeriesFileType.ST_STORAGE_INFLOW
        elif ts_name.value == "pmax_injection":
            time_serie_type = TimeSeriesFileType.ST_STORAGE_INJECTION
        elif ts_name.value == "lower_rule_curve":
            time_serie_type = TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE_
        elif ts_name.value == "upper_rule_curve":
            time_serie_type = TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE
        else:
            time_serie_type = TimeSeriesFileType.ST_STORAGE_WITHDRAWAL

        return read_timeseries(
            time_serie_type,
            self.config.study_path,
            area_id=storage.area_id,
            cluster_id=storage.id,
        )

    @override
    def read_st_storages(self, area_id: str) -> List[STStorage]:
        st_storage_dict = IniFile(
            self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id
        ).ini_dict
        if not st_storage_dict:
            return []
        return [
            STStorage(
                storage_service=self,
                area_id=area_id,
                name=storage.pop("name"),
                properties=STStoragePropertiesLocal.model_validate(storage).to_user_model(),
            )
            for storage in st_storage_dict.values()
        ]

    @override
    def update_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        raise NotImplementedError
