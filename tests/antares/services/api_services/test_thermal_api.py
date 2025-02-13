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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    ThermalMatrixDownloadError,
    ThermalMatrixUpdateError,
    ThermalPropertiesUpdateError,
)
from antares.craft.model.area import Area
from antares.craft.model.study import Study
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
)
from antares.craft.service.api_services.area_api import AreaApiService
from antares.craft.service.api_services.factory import ApiServiceFactory
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.services.thermal import ThermalApiService


@pytest.fixture
def thermal_matrix_set():
    params = [
        ("get_prepro_data_matrix", ThermalClusterMatrixName.PREPRO_DATA, "input/thermal/prepro", "prepro"),
        ("get_prepro_modulation_matrix", ThermalClusterMatrixName.PREPRO_MODULATION, "input/thermal/prepro", "prepro"),
        ("get_series_matrix", ThermalClusterMatrixName.SERIES, "input/thermal/series", "series"),
        ("get_co2_cost_matrix", ThermalClusterMatrixName.SERIES_CO2_COST, "input/thermal/series", "series"),
        ("get_fuel_cost_matrix", ThermalClusterMatrixName.SERIES_FUEL_COST, "input/thermal/series", "series"),
    ]
    return params


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    factory = ApiServiceFactory(api, study_id)
    study = Study("study_test", "870", factory)
    area = Area(
        "area-test",
        factory.create_area_service(),
        factory.create_st_storage_service(),
        factory.create_thermal_service(),
        factory.create_renewable_service(),
        factory.create_hydro_service(),
    )
    thermal = ThermalCluster(factory.create_thermal_service(), "area-test", "thermal-test")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_thermal_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = ThermalClusterPropertiesUpdate(co2=4)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/"
                f"areas/{self.thermal.area_id}/clusters/thermal/{self.thermal.id}"
            )
            mocker.patch(url, json={"id": "id", "name": "name", "co2": 4}, status_code=200)
            self.thermal.update_properties(properties=properties)

    def test_update_thermal_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            properties = ThermalClusterProperties(co2=4)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/"
                f"areas/{self.thermal.area_id}/clusters/thermal/{self.thermal.id}"
            )
            antares_web_description_msg = "Server KO"
            mocker.patch(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ThermalPropertiesUpdateError,
                match=f"Could not update properties for thermal cluster "
                f"{self.thermal.id} inside area {self.area.id}: {antares_web_description_msg}",
            ):
                self.thermal.update_properties(properties=properties)

    def test_get_thermal_matrices_success(self, thermal_matrix_set):
        for matrix_method, matrix_enum, path, path_suffix in thermal_matrix_set:
            with requests_mock.Mocker() as mocker:
                url = (
                    f"https://antares.com/api/v1/studies/{self.study_id}"
                    f"/raw?path=input/thermal/{path_suffix}/"
                    f"{self.thermal.area_id}/{self.thermal.name}/{matrix_enum.value}"
                )
                mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
                result_matrix = getattr(self.thermal, matrix_method)()
                assert result_matrix.equals(self.matrix)

    def test_get_thermal_matrices_fails(self, thermal_matrix_set):
        for matrix_method, matrix_enum, path, path_suffix in thermal_matrix_set:
            with requests_mock.Mocker() as mocker:
                url = (
                    f"https://antares.com/api/v1/studies/{self.study_id}"
                    f"/raw?path=input/thermal/{path_suffix}/"
                    f"{self.thermal.area_id}/{self.thermal.name}/{matrix_enum.value}"
                )
                mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
                with pytest.raises(
                    ThermalMatrixDownloadError,
                    match=f"Could not download {matrix_enum.value} for cluster {self.thermal.name}"
                    f" inside area {self.area.id}: {self.antares_web_description_msg}",
                ):
                    getattr(self.thermal, matrix_method)()

    def test_upload_thermal_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/series"
            )
            mocker.post(url, status_code=200)
            self.thermal.update_thermal_matrix(self.matrix)

    def test_upload_thermal_matrix_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/series"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload matrix for cluster {self.thermal.name} inside area {self.area.name}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.update_thermal_matrix(self.matrix)

    def test_read_thermals(self):
        json_thermal = [
            {
                "id": "therm_un",
                "group": "Gas",
                "name": "therm_un",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
            }
        ]
        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        area_id = "zone"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/areas/{area_id}/"

        with requests_mock.Mocker() as mocker:
            mocker.get(url + "clusters/thermal", json=json_thermal)

            thermal_api = ThermalApiService(self.api, study_id_test)
            renewable_service = Mock()
            storage_service = Mock()
            hydro_service = Mock()
            area_api = AreaApiService(
                self.api, study_id_test, storage_service, thermal_api, renewable_service, hydro_service
            )

            actual_thermal_list = thermal_api.read_thermal_clusters(area_id)

            thermal_id = json_thermal[0].pop("id")
            thermal_name = json_thermal[0].pop("name")

            thermal_props = ThermalClusterPropertiesAPI(**json_thermal[0]).to_user_model()
            expected_thermal = ThermalCluster(area_api.thermal_service, thermal_id, thermal_name, thermal_props)

            assert len(actual_thermal_list) == 1
            actual_thermal = actual_thermal_list[0]

            assert expected_thermal.id == actual_thermal.id
            assert expected_thermal.name == actual_thermal.name
