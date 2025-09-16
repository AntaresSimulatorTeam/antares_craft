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
    RenewableMatrixDownloadError,
    RenewableMatrixUpdateError,
)
from antares.craft.model.area import Area
from antares.craft.model.renewable import RenewableCluster, RenewableClusterPropertiesUpdate
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.services.area import AreaApiService
from antares.craft.service.api_services.services.renewable import RenewableApiService


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
    renewable = RenewableCluster(services.renewable_service, area.id, "onshore_fr")
    renewable_1 = RenewableCluster(services.renewable_service, area.id, "at_solar_pv")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_renewable_properties_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            properties = RenewableClusterPropertiesUpdate(enabled=False)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/renewables"
            mocker.put(url, json={f"{self.renewable.area_id} / {self.renewable.id}": {"enabled": False}})
            self.renewable.update_properties(properties=properties)

    def test_update_renewable_properties_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            properties = RenewableClusterPropertiesUpdate(enabled=False)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/renewables"
            antares_web_description_msg = "Server KO"
            mocker.put(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the renewable clusters from study '{self.study_id}' : {antares_web_description_msg}",
            ):
                self.renewable.update_properties(properties=properties)

    def test_get_renewable_matrices_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            renewable_matrix = self.renewable.get_timeseries()
            assert renewable_matrix.equals(self.matrix)

    def test_get_renewable_matrices_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                RenewableMatrixDownloadError,
                match=f"Could not download matrix for cluster '{self.renewable.name}' inside area '{self.area.id}'"
                f": {self.antares_web_description_msg}",
            ):
                self.renewable.get_timeseries()

    def test_update_renewable_matrices_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.post(url, status_code=200)
            self.renewable.set_series(self.matrix)

    def test_update_renewable_matrices_fail(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/renewables/series/"
                f"{self.area.id}/{self.renewable.name}/series"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                RenewableMatrixUpdateError,
                match=f"Could not upload matrix for cluster '{self.renewable.name}' inside area '{self.area.name}': "
                + self.antares_web_description_msg,
            ):
                self.renewable.set_series(self.matrix)

    def test_read_renewables(self) -> None:
        json_renewable = {
            "zone / test_renouvelable": {
                "group": "solar thermal",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
                "tsInterpretation": "power-generation",
            }
        }

        study_id_test = "248bbb99-c909-47b7-b239-01f6f6ae7de7"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/table-mode/renewables"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_renewable)
            renewable_api = RenewableApiService(self.api, study_id_test)
            storage_service = Mock()
            thermal_service = Mock()
            hydro_service = Mock()
            area_api = AreaApiService(
                self.api, study_id_test, storage_service, thermal_service, renewable_api, hydro_service
            )

            actual_renewables = renewable_api.read_renewables()

            area_id, renewable_id = list(json_renewable.keys())[0].split(" / ")

            renewable_props = RenewableClusterPropertiesAPI.model_validate(
                list(json_renewable.values())[0]
            ).to_user_model()
            expected_renewable = RenewableCluster(area_api.renewable_service, area_id, renewable_id, renewable_props)

            assert len(actual_renewables) == 1
            actual_renewable = actual_renewables[area_id]["test_renouvelable"]

            assert expected_renewable.id == actual_renewable.id
            assert expected_renewable.name == actual_renewable.name

    def test_update_renewable_clusters_success(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/renewables"
        dict_renewables = {"onshore_fr": self.renewable, "at_solar_pv": self.renewable_1}
        json_renewables = {
            "study_test / onshore_fr": {
                "enabled": True,
                "unitCount": 1,
                "nominalCapacity": 13800,
                "group": "solar pv",
                "tsInterpretation": "production-factor",
            },
            "study_test / at_solar_pv": {
                "enabled": False,
                "unitCount": 1,
                "nominalCapacity": 0,
                "group": "solar thermal",
                "tsInterpretation": "production-factor",
            },
        }

        json_renewables_1 = {
            "onshore_fr": {
                "enabled": True,
                "unit_count": 1,
                "nominal_capacity": 13800,
                "group": "solar pv",
                "ts_interpretation": "production-factor",
            },
            "at_solar_pv": {
                "enabled": False,
                "unit_count": 1,
                "nominal_capacity": 0,
                "group": "solar thermal",
                "ts_interpretation": "production-factor",
            },
        }

        self.study._areas["study_test"] = self.area
        self.study._areas["study_test"]._renewables["onshore_fr"] = self.renewable
        self.study._areas["study_test"]._renewables["at_solar_pv"] = self.renewable_1

        with requests_mock.Mocker() as mocker:
            updated_renewable = {}
            for cluster, props in json_renewables_1.items():
                renewable_update = RenewableClusterPropertiesUpdate(**props)  # type: ignore
                renewable = dict_renewables[cluster]
                updated_renewable[renewable] = renewable_update

            mocker.put(url, json=json_renewables)

            self.study.update_renewable_clusters(updated_renewable)

            renewable_1 = self.study._areas["study_test"]._renewables["onshore_fr"]
            renewable_2 = self.study._areas["study_test"]._renewables["at_solar_pv"]

            assert renewable_1.properties.unit_count == json_renewables["study_test / onshore_fr"]["unitCount"]
            assert renewable_1.properties.enabled == json_renewables["study_test / onshore_fr"]["enabled"]
            assert renewable_1.properties.group.value == json_renewables["study_test / onshore_fr"]["group"]

            assert renewable_2.properties.unit_count == json_renewables["study_test / at_solar_pv"]["unitCount"]
            assert renewable_2.properties.enabled == json_renewables["study_test / at_solar_pv"]["enabled"]
            assert renewable_2.properties.group.value == json_renewables["study_test / at_solar_pv"]["group"]

    def test_update_renewable_clusters_fail(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/renewables"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=400)

            with pytest.raises(
                ClustersPropertiesUpdateError,
                match=f"Could not update properties of the renewable clusters from study '{self.study_id}' : {self.antares_web_description_msg}",
            ):
                self.study.update_renewable_clusters({})
