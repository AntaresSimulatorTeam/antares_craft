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

import numpy as np
import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import MatrixDownloadError, MatrixUploadError
from antares.craft.model.area import Area
from antares.craft.service.api_services.area_api import AreaApiService
from antares.craft.service.service_factory import ServiceFactory


class TestMatrixAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    area = Area(
        "area_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )
    area_api = AreaApiService(api, "248bbb99-c909-47b7-b239-01f6f6ae7de7")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    # =======================
    #  LOAD
    # =======================

    def test_get_load_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            load_matrix = self.area.get_load_matrix()
            assert load_matrix.equals(self.matrix)

    def test_get_load_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading load matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_load_matrix()

    def test_create_load_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_load(pd.DataFrame(data=np.ones((8760, 1))))

    def test_create_load_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading load matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_load(pd.DataFrame(data=np.ones((8760, 1))))

    def test_upload_wrongly_formatted_load_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading load matrix for area {self.area.id}: Expected 8760 rows and received 1.",
            ):
                self.area.create_load(self.matrix)

    # =======================
    #  WIND
    # =======================

    def test_get_wind_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/wind/series/wind_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            wind_matrix = self.area.get_wind_matrix()
            assert wind_matrix.equals(self.matrix)

    def test_create_wind_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/wind/series/wind_{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_wind(self.matrix)

    def test_get_wind_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/wind/series/wind_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading wind matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_wind_matrix()

    def test_create_wind_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/wind/series/wind_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading wind matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_wind(self.matrix)

    # =======================
    #  RESERVES
    # =======================

    def test_get_reserves_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/reserves/{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            reserves_matrix = self.area.get_reserves_matrix()
            assert reserves_matrix.equals(self.matrix)

    def test_create_reserves_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/reserves/{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_reserves(self.matrix)

    def test_get_reserves_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/reserves/{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading reserves matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_reserves_matrix()

    def test_create_reserves_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/reserves/{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading reserves matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_reserves(self.matrix)

    # =======================
    #  SOLAR
    # =======================

    def test_get_solar_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/solar/series/solar_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            solar_matrix = self.area.get_solar_matrix()
            assert solar_matrix.equals(self.matrix)

    def test_create_solar_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/solar/series/solar_{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_solar(self.matrix)

    def test_get_solar_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/solar/series/solar_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading solar matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_solar_matrix()

    def test_create_solar_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/solar/series/solar_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading solar matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_solar(self.matrix)

    # =======================
    #  MISC GEN
    # =======================

    def test_get_misc_gen_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/misc-gen/miscgen-{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            misc_gen_matrix = self.area.get_misc_gen_matrix()
            assert misc_gen_matrix.equals(self.matrix)

    def test_create_misc_gen_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/misc-gen/miscgen-{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_misc_gen(self.matrix)

    def test_get_misc_gen_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/misc-gen/miscgen-{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading misc-gen matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_misc_gen_matrix()

    def test_create_misc_gen_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/misc-gen/miscgen-{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading misc-gen matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_misc_gen(self.matrix)
