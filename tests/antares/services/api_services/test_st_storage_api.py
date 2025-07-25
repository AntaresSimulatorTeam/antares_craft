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

from unittest.mock import Mock

import pandas as pd

from antares.craft import Study
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    ClustersPropertiesUpdateError,
    STStorageMatrixDownloadError,
    STStorageMatrixUploadError,
)
from antares.craft.model.area import Area
from antares.craft.model.st_storage import STStorage, STStoragePropertiesUpdate
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.st_storage import parse_st_storage_api
from antares.craft.service.api_services.services.area import AreaApiService
from antares.craft.service.api_services.services.st_storage import ShortTermStorageApiService


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    services = create_api_services(api, study_id)
    study = Study("study_test", "880", services)
    area = Area(
        "study_test",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    storage = STStorage(services.short_term_storage_service, area.id, "battery_fr")
    storage_1 = STStorage(services.short_term_storage_service, area.id, "duracell")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_st_storage_properties_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            properties = STStoragePropertiesUpdate(enabled=False)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/st-storages"
            mocker.put(
                url, json={f"{self.storage.area_id} / {self.storage.area_id}": {"enabled": False}}, status_code=200
            )
            self.study.update_st_storages({self.storage: properties})

    def test_update_st_storage_properties_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            properties = STStoragePropertiesUpdate(enabled=False)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/st-storages"
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the short term storage clusters from study '{self.study_id}' : {self.antares_web_description_msg}",
            ):
                self.study.update_st_storages({self.storage: properties})

    def test_get_storage_matrix_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/st-storage/series/{self.area.id}/{self.storage.id}/inflows"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            inflow_matrix = self.storage.get_storage_inflows()
            assert inflow_matrix.equals(self.matrix)

    def test_get_storage_matrix_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/st-storage/series/{self.area.id}/{self.storage.id}/inflows"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                STStorageMatrixDownloadError,
                match=f"Could not download inflows matrix for storage '{self.storage.id}' "
                f"inside area '{self.area.id}': {self.antares_web_description_msg}",
            ):
                self.storage.get_storage_inflows()

    def test_update_storage_matrix_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/st-storage/series/{self.area.id}/{self.storage.id}/inflows"
            mocker.post(url, status_code=200)
            self.storage.set_storage_inflows(self.matrix)

    def test_update_storage_matrix_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/st-storage/series/{self.area.id}/{self.storage.id}/inflows"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                STStorageMatrixUploadError,
                match=f"Could not upload inflows matrix for storage '{self.storage.id}' inside area '{self.area.id}':"
                f" {self.antares_web_description_msg}",
            ):
                self.storage.set_storage_inflows(self.matrix)

    def test_read_st_storages(self) -> None:
        json_storage = {
            "zone / test_storage": {
                "group": "pondage",
                "injectionNominalCapacity": 0,
                "withdrawalNominalCapacity": 0,
                "reservoirCapacity": 0,
                "efficiency": 1,
                "initialLevel": 0.5,
                "initialLevelOptim": "false",
                "enabled": "true",
            }
        }
        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/table-mode/st-storages"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_storage)

            storage_api = ShortTermStorageApiService(self.api, study_id_test)
            renewable_service = Mock()
            thermal_service = Mock()
            hydro_service = Mock()
            area_api = AreaApiService(
                self.api, study_id_test, storage_api, thermal_service, renewable_service, hydro_service
            )

            actual_storages = storage_api.read_st_storages()

            area_id, storage_id = list(json_storage.keys())[0].split(" / ")

            storage_props = parse_st_storage_api(list(json_storage.values())[0])
            expected_st_storage = STStorage(area_api.storage_service, area_id, storage_id, storage_props)

            assert len(actual_storages) == 1
            actual_st_storage = actual_storages[area_id]["test_storage"]

            assert expected_st_storage.id == actual_st_storage.id
            assert expected_st_storage.name == actual_st_storage.name

    def test_update_st_storages_properties_success(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/st-storages"
        dict_st_storages = {"battery_fr": self.storage, "duracell": self.storage_1}

        json_storages = {
            "study_test / battery_fr": {
                "group": "psp_open",
                "injectionNominalCapacity": 0,
                "withdrawalNominalCapacity": 0,
                "reservoirCapacity": 0,
                "efficiency": 1,
                "initialLevel": 0.5,
                "initialLevelOptim": False,
            },
            "study_test / duracell": {
                "group": "battery",
                "injectionNominalCapacity": 470,
                "withdrawalNominalCapacity": 470,
                "reservoirCapacity": 940,
                "efficiency": 0.8996,
                "initialLevel": 0.54,
                "initialLevelOptim": False,
            },
        }
        json_storages_1 = {
            "battery_fr": {
                "group": "psp_open",
                "injection_nominal_capacity": 0,
                "withdrawal_nominal_capacity": 0,
                "reservoir_capacity": 0,
                "efficiency": 1,
                "initial_level": 0.5,
                "initial_level_optim": False,
            },
            "duracell": {
                "group": "battery",
                "injection_nominal_capacity": 470,
                "withdrawal_nominal_capacity": 470,
                "reservoir_capacity": 940,
                "efficiency": 0.8996,
                "initial_level": 0.54,
                "initial_level_optim": False,
            },
        }
        self.study._areas["study_test"] = self.area
        self.study._areas["study_test"]._st_storages["battery_fr"] = self.storage
        self.study._areas["study_test"]._st_storages["duracell"] = self.storage_1

        with requests_mock.Mocker() as mocker:
            updated_storages = {}
            for cluster, props in json_storages_1.items():
                storage_update = STStoragePropertiesUpdate(**props)  # type: ignore
                storage = dict_st_storages[cluster]
                updated_storages[storage] = storage_update

            mocker.put(url, json=json_storages, status_code=200)

            self.study.update_st_storages(updated_storages)

            storage = self.study._areas["study_test"]._st_storages["battery_fr"]
            storage_1 = self.study._areas["study_test"]._st_storages["duracell"]

            assert storage.properties.initial_level == json_storages["study_test / battery_fr"]["initialLevel"]
            assert storage.properties.efficiency == json_storages["study_test / battery_fr"]["efficiency"]
            assert storage.properties.group == json_storages["study_test / battery_fr"]["group"]

            assert storage_1.properties.initial_level == json_storages["study_test / duracell"]["initialLevel"]
            assert storage_1.properties.efficiency == json_storages["study_test / duracell"]["efficiency"]
            assert storage_1.properties.group == json_storages["study_test / duracell"]["group"]

    def test_update_st_storages_properties_fail(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/st-storages"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=400)
            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the short term storage clusters from study '{self.study_id}' : {self.antares_web_description_msg}",
            ):
                self.study.update_st_storages({})
