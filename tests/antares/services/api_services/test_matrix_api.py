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
from antares.craft.model.hydro import Hydro, HydroProperties
from antares.craft.service.api_services.factory import ApiServiceFactory
from antares.craft.service.service_factory import ServiceFactory


class TestMatrixAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    factory = ApiServiceFactory(api, study_id)
    area = Area(
        "area_test",
        factory.create_area_service(),
        factory.create_st_storage_service(),
        factory.create_thermal_service(),
        factory.create_renewable_service(),
        factory.create_hydro_service(),
    )

    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])
    hydro = Hydro(factory.create_hydro_service(), "area_test", properties=HydroProperties())

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

    # =======================
    #  MAXPOWER
    # =======================

    def test_get_maxpower_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/maxpower_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            matrix_maxpower = self.hydro.get_maxpower()
            assert matrix_maxpower.equals(self.matrix)

    def test_get_maxpower_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/maxpower_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading maxpower matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_maxpower()

    # =======================
    #  RESERVOIR
    # =======================

    def test_get_reservoir_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/reservoir_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            reservoir_matrix = self.hydro.get_reservoir()
            assert reservoir_matrix.equals(self.matrix)

    def test_get_reservoir_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/reservoir_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading reservoir matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_reservoir()

    # =======================
    #  INFLOW PATTERNS
    # =======================

    def test_get_inflow_pattern_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/inflowPattern_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            inflow_matrix = self.hydro.get_inflow_pattern()
            assert inflow_matrix.equals(self.matrix)

    def test_get_inflow_pattern_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/inflowPattern_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading inflow_pattern matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_inflow_pattern()

    # =======================
    #  WATER VALUES
    # =======================

    def test_get_water_values_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/waterValues_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            water_values_matrix = self.hydro.get_water_values()
            assert water_values_matrix.equals(self.matrix)

    def test_get_water_values_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/waterValues_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading water_values matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_water_values()

    # =======================
    #  CREDIT MODULATIONS
    # =======================

    def test_get_credit_modulations_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/creditmodulations_{self.area.id}"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            credit_matrix = self.hydro.get_credit_modulations()
            assert credit_matrix.equals(self.matrix)

    def test_get_credit_modulations_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/creditmodulations_{self.area.id}"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading credit_modulations matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_credit_modulations()
