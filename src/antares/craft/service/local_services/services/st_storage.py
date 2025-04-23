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
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType

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

    def _get_ini_path(self, area_id: str) -> Path:
        return self.config.study_path / "input" / "st-storage" / "clusters" / area_id / "list.ini"

    def read_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_ini_path(area_id))

    def save_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self._get_ini_path(area_id))

    @override
    def read_st_storages(self) -> dict[str, dict[str, STStorage]]:
        st_storages: dict[str, dict[str, STStorage]] = {}
        cluster_path = self.config.study_path / "input" / "st-storage" / "clusters"
        if not cluster_path.exists():
            return {}
        for folder in cluster_path.iterdir():
            if folder.is_dir():
                area_id = folder.name

                storage_dict = self.read_ini(area_id)

                for storage_data in storage_dict.values():
                    st_storage = STStorage(
                        storage_service=self,
                        area_id=area_id,
                        name=storage_data["name"],
                        properties=STStoragePropertiesLocal.model_validate(storage_data).to_user_model(),
                    )
                    st_storages.setdefault(area_id, {})[st_storage.id] = st_storage

        return st_storages

    @override
    def set_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        checks_matrix_dimensions(matrix, f"storage/{storage.area_id}/{storage.name}", ts_name.value)
        write_timeseries(self.config.study_path, matrix, MAPPING[ts_name], storage.area_id, storage.id)

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        return read_timeseries(MAPPING[ts_name], self.config.study_path, area_id=storage.area_id, cluster_id=storage.id)

    @override
    def update_st_storages_properties(
        self, new_properties: dict[STStorage, STStoragePropertiesUpdate]
    ) -> dict[STStorage, STStorageProperties]:
        new_properties_dict: dict[STStorage, STStorageProperties] = {}
        cluster_name_to_object: dict[str, STStorage] = {}

        properties_by_areas: dict[str, dict[str, STStoragePropertiesUpdate]] = {}

        for sts, properties in new_properties.items():
            properties_by_areas.setdefault(sts.area_id, {})[sts.name] = properties
            cluster_name_to_object[sts.name] = sts

        for area_id, value in properties_by_areas.items():
            all_storage_name = set(value.keys())  # used to raise an Exception if a storage doesn't exist
            st_storage_dict = self.read_ini(area_id)
            for storage in st_storage_dict.values():
                storage_name = storage["name"]
                if storage_name in value:
                    all_storage_name.remove(storage_name)

                    # Update properties
                    upd_properties = STStoragePropertiesLocal.from_user_model(value[storage_name])
                    upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_unset=True)
                    storage.update(upd_props_as_dict)

                    # Prepare the object to return
                    local_dict = copy.deepcopy(storage)
                    del local_dict["name"]
                    local_properties = STStoragePropertiesLocal.model_validate(local_dict)
                    new_properties_dict[cluster_name_to_object[storage_name]] = local_properties.to_user_model()

            if len(all_storage_name) > 0:
                raise STStoragePropertiesUpdateError(
                    next(iter(all_storage_name)), area_id, "The storage does not exist"
                )

            # Update ini file
            self.save_ini(st_storage_dict, area_id)

        return new_properties_dict
