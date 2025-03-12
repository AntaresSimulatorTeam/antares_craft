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
from typing import List

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    STStorageMatrixDownloadError,
    STStorageMatrixUploadError,
    STStoragePropertiesUpdateError,
)
from antares.craft.model.st_storage import (
    STStorage,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.api_services.models.st_storage import STStoragePropertiesAPI
from antares.craft.service.base_services import BaseShortTermStorageService
from typing_extensions import override


class ShortTermStorageApiService(BaseShortTermStorageService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStoragePropertiesUpdate
    ) -> STStorageProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{st_storage.area_id}/storages/{st_storage.id}"
        try:
            api_model = STStoragePropertiesAPI.from_user_model(properties)
            body = api_model.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not body:
                return st_storage.properties

            response = self._wrapper.patch(url, json=body)
            json_response = response.json()
            del json_response["id"]
            del json_response["name"]
            new_api_properties = STStoragePropertiesAPI.model_validate(json_response)
            new_properties = new_api_properties.to_user_model()

        except APIError as e:
            raise STStoragePropertiesUpdateError(st_storage.id, st_storage.area_id, e.message) from e

        return new_properties

    @override
    def set_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{storage.area_id}/storages/{storage.id}/series/{ts_name.value}"
        try:
            body = {
                "data": matrix.to_numpy().tolist(),
                "index": matrix.index.tolist(),
                "columns": matrix.columns.tolist(),
            }
            self._wrapper.put(url, json=body)
        except APIError as e:
            raise STStorageMatrixUploadError(storage.area_id, storage.id, ts_name.value, e.message) from e

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{storage.area_id}/storages/{storage.id}/series/{ts_name.value}"
        try:
            response = self._wrapper.get(url)
            json_df = response.json()
            dataframe = pd.DataFrame(data=json_df["data"], index=json_df["index"], columns=json_df["columns"])
        except APIError as e:
            raise STStorageMatrixDownloadError(storage.area_id, storage.id, ts_name.value, e.message) from e
        return dataframe

    @override
    def read_st_storages(self, area_id: str) -> List[STStorage]:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages"
        json_storage = self._wrapper.get(url).json()
        storages = []

        for storage in json_storage:
            storage_id = storage.pop("id")
            storage_name = storage.pop("name")

            api_props = STStoragePropertiesAPI.model_validate(storage)
            storage_properties = api_props.to_user_model()
            st_storage = STStorage(self, storage_id, storage_name, storage_properties)
            storages.append(st_storage)

        storages.sort(key=lambda storage: storage.id)

        return storages
