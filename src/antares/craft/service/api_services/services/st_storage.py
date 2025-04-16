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

import pandas as pd

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    ClustersPropertiesUpdateError,
    STStorageMatrixDownloadError,
    STStorageMatrixUploadError,
)
from antares.craft.model.st_storage import (
    STStorage,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.api_services.models.st_storage import STStoragePropertiesAPI
from antares.craft.service.base_services import BaseShortTermStorageService


class ShortTermStorageApiService(BaseShortTermStorageService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

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
    def read_st_storages(self) -> dict[str, dict[str, STStorage]]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/st-storages"
        json_storage = self._wrapper.get(url).json()

        storages: dict[str, dict[str, STStorage]] = {}

        for key, storage in json_storage.items():
            area_id, storage_id = key.split(" / ")
            api_props = STStoragePropertiesAPI.model_validate(storage)
            storage_props = api_props.to_user_model()
            st_storage = STStorage(self, area_id, storage_id, storage_props)

            storages.setdefault(area_id, {})[st_storage.id] = st_storage

        return storages

    @override
    def update_st_storages_properties(
        self, new_properties: dict[STStorage, STStoragePropertiesUpdate]
    ) -> dict[STStorage, STStorageProperties]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/st-storages"
        updated_storages: dict[STStorage, STStorageProperties] = {}
        body = {}
        cluster_dict = {}

        for storage, props in new_properties.items():
            api_properties = STStoragePropertiesAPI.from_user_model(props)
            api_dict = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            cluster_id = f"{storage.area_id} / {storage.id}"
            body[cluster_id] = api_dict

            cluster_dict[cluster_id] = storage

        try:
            json_response = self._wrapper.put(url, json=body).json()
            for key, json_properties in json_response.items():
                if key in cluster_dict:  # Currently AntaresWeb returns all clusters not only the modified ones
                    api_properties = STStoragePropertiesAPI.model_validate(json_properties)
                    storage_properties = api_properties.to_user_model()
                    updated_storages.update({cluster_dict[key]: storage_properties})

        except APIError as e:
            raise ClustersPropertiesUpdateError(self.study_id, "short term storage", e.message) from e

        return updated_storages
