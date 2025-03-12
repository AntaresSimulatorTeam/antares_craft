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
from antares.craft.service.api_services.factory import create_api_services


class TestMatrixAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    services = create_api_services(api, study_id)
    area = Area(
        "area_test",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )

    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])
    hydro = Hydro(services.hydro_service, "area_test", properties=HydroProperties())

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
            self.area.set_load(pd.DataFrame(data=np.ones((8760, 1))))

    def test_create_load_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading load matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.set_load(pd.DataFrame(data=np.ones((8760, 1))))

    def test_update_wrongly_formatted_load_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading load matrix for area {self.area.id}: Expected 8760 rows and received 1.",
            ):
                self.area.set_load(self.matrix)

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
            self.area.set_wind(self.matrix)

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
                self.area.set_wind(self.matrix)

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
            self.area.set_reserves(self.matrix)

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
                self.area.set_reserves(self.matrix)

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
            self.area.set_solar(self.matrix)

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
                self.area.set_solar(self.matrix)

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
            self.area.set_misc_gen(self.matrix)

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
                self.area.set_misc_gen(self.matrix)

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

    def test_update_maxpower_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/maxpower_{self.area.id}"
            mocker.post(url, status_code=200)
            self.hydro.set_maxpower(self.matrix)

    def test_update_maxpower_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/maxpower_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading max_power matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_maxpower(self.matrix)

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

    def test_update_reservoir_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/reservoir_{self.area.id}"
            mocker.post(url, status_code=200)
            self.hydro.set_reservoir(self.matrix)

    def test_update_reservoir_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/reservoir_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading reservoir matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_reservoir(self.matrix)

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

    def test_update_inflow_pattern_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/inflowPattern_{self.area.id}"
            mocker.post(url, status_code=200)
            self.hydro.set_inflow_pattern(self.matrix)

    def test_update_inflow_pattern_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/inflowPattern_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading inflow_pattern matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_inflow_pattern(self.matrix)

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

    def test_update_water_values_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/waterValues_{self.area.id}"
            mocker.post(url, status_code=200)
            self.hydro.set_water_values(self.matrix)

    def test_update_water_values_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/waterValues_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading water_values matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_water_values(self.matrix)

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

    def test_update_credit_modulations_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/creditmodulations_{self.area.id}"
            mocker.post(url, status_code=200)
            self.hydro.set_credits_modulation(self.matrix)

    def test_update_credit_modulations_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/common/capacity/creditmodulations_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading credit_modulations matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_credits_modulation(self.matrix)

    # =======================
    #  MINGEN
    # =======================

    def test_update_mingen_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mingen"
            )
            mocker.post(url, status_code=200)
            self.hydro.set_mingen(self.matrix)

    def test_update_mingen_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mingen"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading mingen matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_mingen(self.matrix)

    def test_get_mingen_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mingen"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            mingen_matrix = self.hydro.get_mingen()
            assert mingen_matrix.equals(self.matrix)

    def test_get_mingen_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mingen"
            )
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading mingen matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_mingen()

    # =======================
    #  MOD
    # =======================

    def test_update_mod_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mod"
            mocker.post(url, status_code=200)
            self.hydro.set_mod_series(self.matrix)

    def test_update_mod_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mod"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading mod matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_mod_series(self.matrix)

    def test_get_mod_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mod"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            mod_matrix = self.hydro.get_mod_series()
            assert mod_matrix.equals(self.matrix)

    def test_get_mod_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/mod"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading mod matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_mod_series()

    # =======================
    #  ROR
    # =======================

    def test_update_ror_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/ror"
            mocker.post(url, status_code=200)
            self.hydro.set_ror_series(self.matrix)

    def test_update_ror_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/ror"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading ror matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_ror_series(self.matrix)

    def test_get_ror_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/ror"
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            ror_matrix = self.hydro.get_ror_series()
            assert ror_matrix.equals(self.matrix)

    def test_get_ror_fail(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/series/{self.area.id}/ror"
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading ror matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_ror_series()

    # =======================
    #  ENERGY
    # =======================

    def test_update_energy_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/prepro/{self.area.id}/energy"
            )
            mocker.post(url, status_code=200)
            self.hydro.set_energy(self.matrix)

    def test_update_energy_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/prepro/{self.area.id}/energy"
            )
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixUploadError,
                match=f"Error uploading energy matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.set_energy(self.matrix)

    def test_get_energy_success(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/prepro/{self.area.id}/energy"
            )
            mocker.get(url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)
            energy_matrix = self.hydro.get_energy()
            assert energy_matrix.equals(self.matrix)

    def test_get_energy_fail(self):
        with requests_mock.Mocker() as mocker:
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/hydro/prepro/{self.area.id}/energy"
            )
            mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                MatrixDownloadError,
                match=f"Error downloading energy matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.hydro.get_energy()
