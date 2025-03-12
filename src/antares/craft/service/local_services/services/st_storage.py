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
from antares.craft.exceptions.exceptions import (
    STStoragePropertiesUpdateError,
)
from antares.craft.model.st_storage import (
    STStorage,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.base_services import BaseShortTermStorageService
from antares.craft.service.local_services.models.st_storage import STStoragePropertiesLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override

MAPPING = {
    STStorageMatrixName.PMAX_INJECTION: TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION,
    STStorageMatrixName.PMAX_WITHDRAWAL: TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL,
    STStorageMatrixName.LOWER_CURVE_RULE: TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE,
    STStorageMatrixName.UPPER_RULE_CURVE: TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE,
    STStorageMatrixName.INFLOWS: TimeSeriesFileType.ST_STORAGE_INFLOWS,
}


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStoragePropertiesUpdate
    ) -> STStorageProperties:
        area_id = st_storage.area_id
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id)
        storage_dict = ini_file.ini_dict
        for storage in storage_dict.values():
            if storage["name"] == st_storage.name:
                # Update properties
                upd_properties = STStoragePropertiesLocal.from_user_model(properties)
                upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                storage.update(upd_props_as_dict)

                # Update ini file
                ini_file.ini_dict = storage_dict
                ini_file.write_ini_file()

                # Prepare the object to return
                local_dict = copy.deepcopy(storage)
                del local_dict["name"]
                local_properties = STStoragePropertiesLocal.model_validate(local_dict)

                return local_properties.to_user_model()
        raise STStoragePropertiesUpdateError(st_storage.name, area_id, "The storage does not exist")

    @override
    def read_st_storages(self, area_id: str) -> list[STStorage]:
        storage_dict = IniFile(
            self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id
        ).ini_dict
        if not storage_dict:
            return []

        return [
            STStorage(
                storage_service=self,
                area_id=area_id,
                name=storage_data["name"],
                properties=STStoragePropertiesLocal.model_validate(storage_data).to_user_model(),
            )
            for storage_data in storage_dict.values()
        ]

    @override
    def set_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        checks_matrix_dimensions(matrix, f"storage/{storage.area_id}/{storage.name}", ts_name.value)
        write_timeseries(self.config.study_path, matrix, MAPPING[ts_name], storage.area_id, storage.id)

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        return read_timeseries(MAPPING[ts_name], self.config.study_path, area_id=storage.area_id, cluster_id=storage.id)
