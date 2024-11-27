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

import pytest
import requests_mock

import pandas as pd

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import (
    STStorageMatrixDownloadError,
    STStorageMatrixUploadError,
    STStoragePropertiesUpdateError,
)
from antares.model.area import Area
from antares.model.st_storage import STStorage, STStorageProperties
from antares.service.api_services.area_api import AreaApiService
from antares.service.api_services.st_storage_api import ShortTermStorageApiService
from antares.service.service_factory import ServiceFactory


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    area = Area(
        "study_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )
    storage = STStorage(ServiceFactory(api, study_id).create_st_storage_service(), area.id, "battery_fr")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_st_storage_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = STStorageProperties(enabled=False)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/"
                f"areas/{self.storage.area_id}/storages/{self.storage.id}"
            )
            mocker.patch(url, json={"id": "id", "name": "name", **properties.model_dump()}, status_code=200)
            self.storage.update_properties(properties=properties)

    def test_update_st_storage_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            properties = STStorageProperties(enabled=False)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.storage.area_id}/"
                f"storages/{self.storage.id}"
            )
            antares_web_description_msg = "Server KO"
            mocker.patch(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                STStoragePropertiesUpdateError,
                match=f"Could not update properties for short term storage {self.storage.id} "
                f"inside area {self.area.id}: {antares_web_description_msg}",
            ):
                self.storage.update_properties(properties=properties)

    def test_get_storage_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.storage.area_id}"
                f"/storages/{self.storage.id}/series/inflows"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            inflow_matrix = self.storage.get_storage_inflows()
            assert inflow_matrix.equals(self.matrix)

    def test_get_storage_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.storage.area_id}"
                f"/storages/{self.storage.id}/series/inflows"
            )
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                STStorageMatrixDownloadError,
                match=f"Could not download inflows matrix for storage {self.storage.id} "
                f"inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.storage.get_storage_inflows()

    def test_upload_storage_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.storage.area_id}"
                f"/storages/{self.storage.id}/series/inflows"
            )
            mocker.put(url, status_code=200)
            self.storage.upload_storage_inflows(self.matrix)

    def test_upload_storage_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.storage.area_id}"
                f"/storages/{self.storage.id}/series/inflows"
            )
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                STStorageMatrixUploadError,
                match=f"Could not upload inflows matrix for storage {self.storage.id} inside area {self.area.id}:"
                f" {self.antares_web_description_msg}",
            ):
                self.storage.upload_storage_inflows(self.matrix)

    def test_read_st_storages(self):
        json_storage = [
            {
                "id": "test_storage",
                "group": "Pondage",
                "name": "test_storage",
                "injectionNominalCapacity": 0,
                "withdrawalNominalCapacity": 0,
                "reservoirCapacity": 0,
                "efficiency": 1,
                "initialLevel": 0.5,
                "initialLevelOptim": "false",
                "enabled": "true",
            }
        ]
        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        area_id = "zone"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/areas/{area_id}/"

        with requests_mock.Mocker() as mocker:
            mocker.get(url + "storages", json=json_storage)
            area_api = AreaApiService(self.api, study_id_test)
            storage_api = ShortTermStorageApiService(self.api, self.study_id)

            actual_storage_list = storage_api.read_st_storages(url)

            storage_id = json_storage[0].pop("id")
            storage_name = json_storage[0].pop("name")

            storage_props = STStorageProperties(**json_storage[0])
            expected_st_storage = STStorage(area_api.storage_service, storage_id, storage_name, storage_props)

            assert len(actual_storage_list) == 1
            actual_st_storage = actual_storage_list[0]

            assert expected_st_storage.id == actual_st_storage.id
            assert expected_st_storage.name == actual_st_storage.name
