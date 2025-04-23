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
    ClustersPropertiesUpdateError,
    ThermalMatrixDownloadError,
    ThermalMatrixUpdateError,
)
from antares.craft.model.area import Area
from antares.craft.model.study import Study
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterPropertiesUpdate,
)
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.services.area import AreaApiService
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
    services = create_api_services(api, study_id)
    study = Study("study_test", "880", services)
    area = Area(
        "area-test",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    area_2 = Area(
        "area-test-2",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    thermal = ThermalCluster(services.thermal_service, area.id, "thermal-test")
    thermal_2 = ThermalCluster(services.thermal_service, area_2.id, "thermal-2")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])
    study_url = f"https://antares.com/api/v1/studies/{study_id}"

    def test_update_thermal_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = ThermalClusterPropertiesUpdate(co2=4)
            url = f"{self.study_url}/table-mode/thermals"
            mocker.put(url, json={f"{self.thermal.area_id} / {self.thermal.id}": {"co2": 4}}, status_code=200)
            self.thermal.update_properties(properties=properties)

    def test_update_thermal_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            properties = ThermalClusterPropertiesUpdate(co2=4)
            url = f"{self.study_url}/table-mode/thermals"
            antares_web_description_msg = "Server KO"
            mocker.put(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the thermal clusters from study {self.study_id} : {antares_web_description_msg}",
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

    def test_read_thermals(self):
        json_thermal = {
            "zone / therm_un": {
                "group": "gas",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
            }
        }
        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/table-mode/thermals"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_thermal)

            thermal_api = ThermalApiService(self.api, study_id_test)
            renewable_service = Mock()
            storage_service = Mock()
            hydro_service = Mock()
            area_api = AreaApiService(
                self.api, study_id_test, storage_service, thermal_api, renewable_service, hydro_service
            )

            actual_thermals = thermal_api.read_thermal_clusters()

            area_id, thermal_id = list(json_thermal.keys())[0].split(" / ")

            thermal_props = ThermalClusterPropertiesAPI(**list(json_thermal.values())[0]).to_user_model()
            expected_thermal = ThermalCluster(area_api.thermal_service, area_id, thermal_id, thermal_props)

            assert len(actual_thermals) == 1
            actual_thermal = actual_thermals[area_id]["therm_un"]

            assert expected_thermal.id == actual_thermal.id
            assert expected_thermal.name == actual_thermal.name

    def test_update_prepro_data_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/data"
            )
            mocker.post(url, status_code=200)
            self.thermal.set_prepro_data(self.matrix)

    def test_update_prepro_data_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/data"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload data for cluster {self.thermal.name} inside area {self.area.id}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.set_prepro_data(self.matrix)

    def test_get_prepro_data_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}"
                f"/raw?path=input/thermal/prepro/"
                f"{self.thermal.area_id}/{self.thermal.name}/data"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            result_matrix = self.thermal.get_prepro_data_matrix()
            result_matrix.equals(self.matrix)

    def test_get_prepro_data_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/data"
            )

            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixDownloadError,
                match=f"Could not download data for cluster {self.thermal.name}"
                f" inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.thermal.get_prepro_data_matrix()

    def test_update_prepro_modulation_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/modulation"
            )
            mocker.post(url, status_code=200)
            self.thermal.set_prepro_modulation(self.matrix)

    def test_update_prepro_modulation_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/modulation"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload modulation for cluster {self.thermal.name} inside area {self.area.id}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.set_prepro_modulation(self.matrix)

    def test_get_prepro_modulation_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}"
                f"/raw?path=input/thermal/prepro/"
                f"{self.thermal.area_id}/{self.thermal.name}/modulation"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            result_matrix = self.thermal.get_prepro_modulation_matrix()
            result_matrix.equals(self.matrix)

    def test_get_prepro_modulation_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/prepro/"
                f"{self.area.id}/{self.thermal.name}/modulation"
            )

            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixDownloadError,
                match=f"Could not download modulation for cluster {self.thermal.name}"
                f" inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.thermal.get_prepro_modulation_matrix()

    def test_update_series_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/series"
            )
            mocker.post(url, status_code=200)
            self.thermal.set_series(self.matrix)

    def test_update_series_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/series"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload series for cluster {self.thermal.name} inside area {self.area.id}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.set_series(self.matrix)

    def test_get_series_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}"
                f"/raw?path=input/thermal/series/"
                f"{self.thermal.area_id}/{self.thermal.name}/series"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            result_matrix = self.thermal.get_series_matrix()
            result_matrix.equals(self.matrix)

    def test_get_series_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/series"
            )

            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixDownloadError,
                match=f"Could not download series for cluster {self.thermal.name}"
                f" inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.thermal.get_series_matrix()

    def test_update_co2_cost_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/CO2Cost"
            )
            mocker.post(url, status_code=200)
            self.thermal.set_co2_cost(self.matrix)

    def test_update_co2_cost_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/CO2Cost"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload CO2Cost for cluster {self.thermal.name} inside area {self.area.id}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.set_co2_cost(self.matrix)

    def test_get_co2_cost_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}"
                f"/raw?path=input/thermal/series/"
                f"{self.thermal.area_id}/{self.thermal.name}/CO2Cost"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            result_matrix = self.thermal.get_co2_cost_matrix()
            result_matrix.equals(self.matrix)

    def test_get_co2_cost_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/CO2Cost"
            )

            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixDownloadError,
                match=f"Could not download CO2Cost for cluster {self.thermal.name}"
                f" inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.thermal.get_co2_cost_matrix()

    def test_update_fuel_cost_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/fuelCost"
            )
            mocker.post(url, status_code=200)
            self.thermal.set_fuel_cost(self.matrix)

    def test_update_fuel_cost_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/thermal/series/"
                f"{self.area.id}/{self.thermal.name}/fuelCost"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalMatrixUpdateError,
                match=f"Could not upload fuelCost for cluster {self.thermal.name} inside area {self.area.id}: "
                + self.antares_web_description_msg,
            ):
                self.thermal.set_fuel_cost(self.matrix)

    def test_update_multiple_thermal_clusters_success(self):
        dict_thermals = {"thermal-test": self.thermal, "thermal-2": self.thermal_2}
        json_thermals = {
            "area-test / thermal-test": {
                "enabled": True,
                "unitCount": 1,
                "nominalCapacity": 0,
                "group": "lignite",
                "marginalCost": 0,
            },
            "area-test-2 / thermal-2": {
                "enabled": True,
                "unitCount": 1,
                "nominalCapacity": 1500,
                "group": "nuclear",
                "marginalCost": 10,
            },
        }

        json_thermals_1 = {
            "thermal-test": {
                "enabled": True,
                "unit_count": 1,
                "nominal_capacity": 0,
                "group": "lignite",
                "marginal_cost": 0,
            },
            "thermal-2": {
                "enabled": True,
                "unit_count": 1,
                "nominal_capacity": 1500,
                "group": "nuclear",
                "marginal_cost": 10,
            },
        }

        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/thermals"

        self.study._areas["area-test"] = self.area
        self.study._areas["area-test-2"] = self.area_2
        self.study._areas["area-test"]._thermals["thermal-test"] = self.thermal
        self.study._areas["area-test-2"]._thermals["thermal-2"] = self.thermal_2

        with requests_mock.Mocker() as mocker:
            updated_thermal = {}

            for cluster, props in json_thermals_1.items():
                thermal_update = ThermalClusterPropertiesUpdate(**props)
                thermal = dict_thermals[cluster]
                updated_thermal[thermal] = thermal_update

            mocker.put(url, json=json_thermals)
            self.study.update_thermal_clusters(updated_thermal)

            thermal = self.study._areas["area-test"]._thermals["thermal-test"]
            thermal_1 = self.study._areas["area-test-2"]._thermals["thermal-2"]

            assert thermal.properties.unit_count == json_thermals["area-test / thermal-test"]["unitCount"]
            assert thermal.properties.enabled == json_thermals["area-test / thermal-test"]["enabled"]
            assert thermal.properties.marginal_cost == json_thermals["area-test / thermal-test"]["marginalCost"]

            assert thermal_1.properties.unit_count == json_thermals["area-test-2 / thermal-2"]["unitCount"]
            assert thermal_1.properties.enabled == json_thermals["area-test-2 / thermal-2"]["enabled"]
            assert thermal_1.properties.marginal_cost == json_thermals["area-test-2 / thermal-2"]["marginalCost"]

    def test_update_multiple_thermal_clusters_fail(self):
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/thermals"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=400)

            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the thermal clusters from study {self.study_id} : {self.antares_web_description_msg}",
            ):
                self.study.update_thermal_clusters({})
