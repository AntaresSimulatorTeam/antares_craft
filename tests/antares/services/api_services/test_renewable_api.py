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
    RenewableMatrixDownloadError,
    RenewableMatrixUpdateError,
    RenewablePropertiesUpdateError,
)
from antares.craft.model.area import Area
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesUpdate
from antares.craft.service.api_services.area_api import AreaApiService
from antares.craft.service.api_services.factory import ApiServiceFactory
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.services.renewable import RenewableApiService


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    factory = ApiServiceFactory(api, study_id)
    area = Area(
        "study_test",
        factory.create_area_service(),
        factory.create_st_storage_service(),
        factory.create_thermal_service(),
        factory.create_renewable_service(),
        factory.create_hydro_service(),
    )
    renewable = RenewableCluster(factory.create_renewable_service(), area.id, "onshore_fr")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_renewable_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = RenewableClusterPropertiesUpdate(enabled=False)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.renewable.area_id}/"
                f"clusters/renewable/{self.renewable.id}"
            )
            mocker.patch(url, json={"id": "id", "name": "name", "enabled": False}, status_code=200)
            self.renewable.update_properties(properties=properties)

    def test_update_renewable_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            properties = RenewableClusterProperties(enabled=False)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.renewable.area_id}"
                f"/clusters/renewable/{self.renewable.id}"
            )
            antares_web_description_msg = "Server KO"
            mocker.patch(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                RenewablePropertiesUpdateError,
                match=f"Could not update properties for renewable cluster {self.renewable.id} "
                f"inside area {self.area.id}: {antares_web_description_msg}",
            ):
                self.renewable.update_properties(properties=properties)

    def test_get_renewable_matrices_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            renewable_matrix = self.renewable.get_timeseries()
            assert renewable_matrix.equals(self.matrix)

    def test_get_renewable_matrices_fails(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                RenewableMatrixDownloadError,
                match=f"Could not download matrix for cluster {self.renewable.name} inside area {self.area.id}"
                f": {self.antares_web_description_msg}",
            ):
                self.renewable.get_timeseries()

    def test_upload_renewable_matrices_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.post(url, status_code=200)
            self.renewable.update_renewable_matrix(self.matrix)

    def test_upload_renewable_matrices_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                RenewableMatrixUpdateError,
                match=f"Could not upload matrix for cluster {self.renewable.name} inside area {self.area.name}: "
                + self.antares_web_description_msg,
            ):
                self.renewable.update_renewable_matrix(self.matrix)

    def test_read_renewables(self):
        json_renewable = [
            {
                "id": "test_renouvelable",
                "group": "Solar Thermal",
                "name": "test_renouvelable",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
                "tsInterpretation": "power-generation",
            }
        ]

        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        area_id = "zone"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/areas/{area_id}/"

        with requests_mock.Mocker() as mocker:
            mocker.get(url + "clusters/renewable", json=json_renewable)
            renewable_api = RenewableApiService(self.api, study_id_test)
            storage_service = Mock()
            thermal_service = Mock()
            hydro_service = Mock()
            area_api = AreaApiService(
                self.api, study_id_test, storage_service, thermal_service, renewable_api, hydro_service
            )

            actual_renewable_list = renewable_api.read_renewables(area_id)

            renewable_id = json_renewable[0].pop("id")
            renewable_name = json_renewable[0].pop("name")

            renewable_props = RenewableClusterPropertiesAPI(**json_renewable[0]).to_user_model()
            expected_renewable = RenewableCluster(
                area_api.renewable_service, renewable_id, renewable_name, renewable_props
            )

            assert len(actual_renewable_list) == 1
            actual_renewable = actual_renewable_list[0]

            assert expected_renewable.id == actual_renewable.id
            assert expected_renewable.name == actual_renewable.name
