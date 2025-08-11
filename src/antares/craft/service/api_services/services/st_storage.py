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
    STStorageConstraintCreationError,
    STStorageConstraintDeletionError,
    STStorageConstraintEditionError,
    STStorageMatrixDownloadError,
    STStorageMatrixUploadError,
)
from antares.craft.model.st_storage import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintUpdate,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.api_services.models.st_storage import (
    parse_st_storage_api,
    parse_st_storage_constraint_api,
    serialize_st_storage_api,
    serialize_st_storage_constraint_api,
)
from antares.craft.service.api_services.utils import get_matrix, update_series
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
        series_path = f"input/st-storage/series/{storage.area_id}/{storage.id}/{ts_name.value}"
        try:
            update_series(self._base_url, self.study_id, self._wrapper, matrix, series_path)
        except APIError as e:
            raise STStorageMatrixUploadError(storage.area_id, storage.id, ts_name.value, e.message) from e

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        series_path = f"input/st-storage/series/{storage.area_id}/{storage.id}/{ts_name.value}"
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, series_path)
        except APIError as e:
            raise STStorageMatrixDownloadError(storage.area_id, storage.id, ts_name.value, e.message) from e

    @override
    def read_st_storages(self) -> dict[str, dict[str, STStorage]]:
        # Constraints
        constraints_url = f"{self._base_url}/studies/{self.study_id}/table-mode/st-storages-additional-constraints"
        json_constraints = self._wrapper.get(constraints_url).json()

        constraints_dict: dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]] = {}
        for key, constraint_api in json_constraints.items():
            area_id, storage_id, constraint_id = key.split(" / ")
            args = {"id": constraint_id, "name": constraint_id, **constraint_api}
            constraint = parse_st_storage_constraint_api(args)
            constraints_dict.setdefault(area_id, {}).setdefault(storage_id, {})[constraint.id] = constraint

        # Storages
        storage_url = f"{self._base_url}/studies/{self.study_id}/table-mode/st-storages"
        json_storage = self._wrapper.get(storage_url).json()

        storages: dict[str, dict[str, STStorage]] = {}

        for key, storage in json_storage.items():
            area_id, storage_id = key.split(" / ")
            storage_props = parse_st_storage_api(storage)
            constraints = constraints_dict.get(area_id, {}).get(storage_id, {})
            st_storage = STStorage(self, area_id, storage_id, storage_props, constraints)

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
            api_dict = serialize_st_storage_api(props)
            cluster_id = f"{storage.area_id} / {storage.id}"
            body[cluster_id] = api_dict

            cluster_dict[cluster_id] = storage

        try:
            json_response = self._wrapper.put(url, json=body).json()
            for key, json_properties in json_response.items():
                if key in cluster_dict:  # Currently AntaresWeb returns all clusters not only the modified ones
                    storage_properties = parse_st_storage_api(json_properties)
                    updated_storages.update({cluster_dict[key]: storage_properties})

        except APIError as e:
            raise ClustersPropertiesUpdateError(self.study_id, "short term storage", e.message) from e

        return updated_storages

    @override
    def update_st_storages_constraints(
        self, new_constraints: dict[STStorage, dict[str, STStorageAdditionalConstraintUpdate]]
    ) -> dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/st-storages-additional-constraints"
        body = {}

        constraints_dict: dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]] = {}

        for storage, props in new_constraints.items():
            for constraint_id, constraint_update in props.items():
                api_dict = serialize_st_storage_constraint_api(constraint_update)
                key = f"{storage.area_id} / {storage.id} / {constraint_id}"
                body[key] = api_dict

        try:
            json_response = self._wrapper.put(url, json=body).json()
            for key, json_properties in json_response.items():
                area_id, storage_id, constraint_id = key.split(" / ")
                args = {"id": constraint_id, "name": constraint_id, **json_properties}
                constraint = parse_st_storage_constraint_api(args)

                constraints_dict.setdefault(area_id, {}).setdefault(storage_id, {})[constraint.id] = constraint

        except APIError as e:
            raise STStorageConstraintEditionError(self.study_id, e.message) from e

        return constraints_dict

    @override
    def create_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> list[STStorageAdditionalConstraint]:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages/{storage_id}/additional-constraints"

        try:
            body = [serialize_st_storage_constraint_api(constraint) for constraint in constraints]
            json_response = self._wrapper.post(url, json=body).json()

            return [parse_st_storage_constraint_api(constraint) for constraint in json_response]

        except APIError as e:
            raise STStorageConstraintCreationError(self.study_id, area_id, storage_id, e.message) from e

    @override
    def delete_constraints(self, area_id: str, storage_id: str, constraint_ids: list[str]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages/{storage_id}/additional-constraints"

        try:
            self._wrapper.delete(url, json=constraint_ids)

        except APIError as e:
            raise STStorageConstraintDeletionError(self.study_id, area_id, storage_id, e.message) from e

    @override
    def get_constraint_term(self, area_id: str, storage_id: str, constraint_id: str) -> pd.DataFrame:
        series_path = f"input/st-storage/constraints/{area_id}/{storage_id}/rhs_{constraint_id}"
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, series_path)
        except APIError as e:
            raise STStorageMatrixDownloadError(area_id, storage_id, f"constraint {constraint_id}", e.message) from e

    @override
    def set_constraint_term(self, area_id: str, storage_id: str, constraint_id: str, matrix: pd.DataFrame) -> None:
        series_path = f"input/st-storage/constraints/{area_id}/{storage_id}/rhs_{constraint_id}"
        try:
            update_series(self._base_url, self.study_id, self._wrapper, matrix, series_path)
        except APIError as e:
            raise STStorageMatrixUploadError(area_id, storage_id, f"constraint {constraint_id}", e.message) from e
