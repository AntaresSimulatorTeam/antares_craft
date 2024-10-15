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
from antares.exceptions.exceptions import RenewableMatrixDownloadError, RenewablePropertiesUpdateError
from antares.model.area import Area
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
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
    renewable = RenewableCluster(ServiceFactory(api, study_id).create_renewable_service(), area.id, "onshore_fr")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_renewable_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = RenewableClusterProperties(enabled=False)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.renewable.area_id}/"
                f"clusters/renewable/{self.renewable.id}"
            )
            mocker.patch(url, json={"id": "id", "name": "name", **properties.model_dump()}, status_code=200)
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
            renewable_matrix = self.renewable.get_renewable_matrix()
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
                self.renewable.get_renewable_matrix()
