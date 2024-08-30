import json

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import (
    ThermalCreationError,
    RenewableCreationError,
    STStorageCreationError,
    AreaPropertiesUpdateError,
    AreaUiUpdateError,
    LoadMatrixDownloadError,
    LoadMatrixUploadError,
    MatrixUploadError,
)
from antares.model.area import Area, AreaUi, AreaProperties
from antares.model.hydro import HydroMatrixName, HydroProperties, Hydro
from antares.model.renewable import RenewableClusterProperties, RenewableCluster
from antares.model.st_storage import STStorageProperties, STStorage
from antares.model.thermal import ThermalClusterProperties, ThermalCluster
from antares.service.service_factory import ServiceFactory
import requests_mock

import pytest
import pandas as pd
import numpy as np


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    area = Area(
        "area_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_area_properties_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/properties/form"
            properties = AreaProperties()
            mocker.put(url, status_code=200)
            mocker.get(url, json=properties, status_code=200)
            self.area.update_properties(properties=properties)

    def test_update_area_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/properties/form"
            properties = AreaProperties()
            properties.energy_cost_unsupplied = 100
            antares_web_description_msg = "Server KO"
            mocker.put(url, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                AreaPropertiesUpdateError,
                match=f"Could not update properties for area {self.area.id}: {antares_web_description_msg}",
            ):
                self.area.update_properties(properties=properties)

    def test_update_area_ui_success(self):
        with requests_mock.Mocker() as mocker:
            ui = AreaUi(layerX={"1": 0}, layerY={"1": 0}, layerColor={"1": "0"})
            url1 = f"https://antares.com/api/v1/studies/{self.study_id}/areas?type=AREA&ui=true"
            ui_info = {"ui": {"x": 0, "y": 0, "layers": 0, "color_r": 0, "color_g": 0, "color_b": 0}}
            area_ui = {**ui.model_dump(by_alias=True), **ui_info}
            mocker.get(url1, json={self.area.id: area_ui}, status_code=201)
            url2 = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/ui"
            mocker.put(url2, status_code=200)

            self.area.update_ui(ui)

    def test_update_area_ui_fails(self):
        with requests_mock.Mocker() as mocker:
            ui = AreaUi(layerX={"1": 0}, layerY={"1": 0}, layerColor={"1": "0"})
            url1 = f"https://antares.com/api/v1/studies/{self.study_id}/areas?type=AREA&ui=true"
            ui_info = {"ui": {"x": 0, "y": 0, "layers": 0, "color_r": 0, "color_g": 0, "color_b": 0}}
            area_ui = {**ui.model_dump(by_alias=True), **ui_info}
            mocker.get(url1, json={self.area.id: area_ui}, status_code=201)
            url2 = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/ui"
            antares_web_description_msg = "Server KO"
            mocker.put(url2, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                AreaUiUpdateError,
                match=f"Could not update ui for area {self.area.id}: {antares_web_description_msg}",
            ):
                self.area.update_ui(ui)

    def test_create_thermal_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/clusters/thermal"
            json_response = json.loads(ThermalClusterProperties().model_dump_json(by_alias=True))
            thermal_name = "thermal_cluster"
            mocker.post(url, json={"name": thermal_name, "id": thermal_name, **json_response}, status_code=201)
            thermal = self.area.create_thermal_cluster(thermal_name=thermal_name)
            assert isinstance(thermal, ThermalCluster)

    def test_create_thermal_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/clusters/thermal"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            thermal_name = "thermal_cluster"

            with pytest.raises(
                ThermalCreationError,
                match=f"Could not create the thermal cluster {thermal_name} inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_thermal_cluster(thermal_name=thermal_name)

    def test_create_renewable_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/clusters/renewable"
            json_response = json.loads(RenewableClusterProperties().model_dump_json(by_alias=True))
            renewable_name = "renewable_cluster"
            mocker.post(url, json={"name": renewable_name, "id": renewable_name, **json_response}, status_code=201)

            renewable = self.area.create_renewable_cluster(
                renewable_name=renewable_name, properties=RenewableClusterProperties(), series=None
            )
            assert isinstance(renewable, RenewableCluster)

    def test_create_renewable_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/clusters/renewable"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            renewable_name = "renewable_cluster"

            with pytest.raises(
                RenewableCreationError,
                match=f"Could not create the renewable cluster {renewable_name} inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_renewable_cluster(
                    renewable_name=renewable_name, properties=RenewableClusterProperties(), series=None
                )

    def test_create_st_storage_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/storages"
            json_response = json.loads(STStorageProperties().model_dump_json(by_alias=True))
            st_storage_name = "short_term_storage"
            mocker.post(url, json={"name": st_storage_name, "id": st_storage_name, **json_response}, status_code=201)

            st_storage = self.area.create_st_storage(st_storage_name=st_storage_name)
            assert isinstance(st_storage, STStorage)

    def test_create_st_storage_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/storages"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            st_storage_name = "short_term_storage"

            with pytest.raises(
                STStorageCreationError,
                match=f"Could not create the short term storage {st_storage_name} inside area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.create_st_storage(st_storage_name=st_storage_name)

    def test_create_thermal_cluster_with_matrices(self):
        expected_url = f"https://antares.com/api/v1/studies/{self.study_id}/commands"
        matrix_test = pd.DataFrame(data=np.ones((8760, 1)))
        json_for_post = (
            [
                {
                    "action": "create_cluster",
                    "args": {
                        "area_id": "fr",
                        "cluster_name": "cluster 1",
                        "parameters": {},
                        "prepro": matrix_test.to_dict(orient="split"),
                        "modulation": matrix_test.to_dict(orient="split"),
                    },
                }
            ],
        )
        with requests_mock.Mocker() as mocker:
            mocker.post(expected_url, json=json_for_post, status_code=200)

            thermal_cluster = self.area.create_thermal_cluster_with_matrices(
                cluster_name="cluster_test",
                parameters=ThermalClusterProperties(),
                prepro=matrix_test,
                modulation=matrix_test,
                series=matrix_test,
                CO2Cost=matrix_test,
                fuelCost=matrix_test,
            )
            # to assert two http requests to "commands"
            assert len(mocker.request_history) == 2
            assert isinstance(thermal_cluster, ThermalCluster)

    def test_create_hydro_success(self):
        url_hydro_form = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/hydro/form"
        json_for_post = json.loads(HydroProperties().model_dump_json(by_alias=True))
        series = pd.DataFrame(data=np.ones((150, 1)))

        url_for_command = f"https://antares.com/api/v1/studies/{self.study_id}/commands"

        matrices_hydro = {
            HydroMatrixName.SERIES_ROR: series,
            HydroMatrixName.SERIES_MOD: series,
            HydroMatrixName.SERIES_MIN_GEN: series,
            HydroMatrixName.PREPRO_ENERGY: series,
            HydroMatrixName.COMMON_WATER_VALUES: series,
            HydroMatrixName.COMMON_RESERVOIR: series,
            HydroMatrixName.COMMON_MAX_POWER: series,
            HydroMatrixName.COMMON_INFLOW_PATTERN: series,
            HydroMatrixName.COMMON_CREDIT_MODULATIONS: series,
        }
        with requests_mock.Mocker() as mocker:
            mocker.put(url_hydro_form, json=json_for_post, status_code=200)
            mocker.post(url_for_command)
            hydro = self.area.create_hydro(properties=HydroProperties(), matrices=matrices_hydro)
            # to assert two http requests to "commands" and "hydro/form"
            assert len(mocker.request_history) == 2
            assert isinstance(hydro, Hydro)

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
                LoadMatrixDownloadError,
                match=f"Could not download load matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.get_load_matrix()

    def test_upload_load_matrix_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.upload_load_matrix(pd.DataFrame(data=np.ones((8760, 1))))

    def test_upload_load_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                LoadMatrixUploadError,
                match=f"Could not upload load matrix for area {self.area.id}: {self.antares_web_description_msg}",
            ):
                self.area.upload_load_matrix(pd.DataFrame(data=np.ones((8760, 1))))

    def test_upload_wrong_load_matrix_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/load/series/load_{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                LoadMatrixUploadError,
                match=f"Could not upload load matrix for area {self.area.id}: Expected 8760 rows and received 1.",
            ):
                self.area.upload_load_matrix(self.matrix)

    def test_create_wind_success(self):
        with requests_mock.Mocker() as mocker:
            expected_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/" f"raw?path=input/wind/series/wind_area_test"
            )
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=" f"input/wind/series/wind_{self.area.id}"
            )
            mocker.post(url, status_code=200)
            self.area.create_wind(series=self.matrix)

            assert mocker.request_history[0].url == expected_url

    def test_create_reserves_success(self):
        with requests_mock.Mocker() as mocker:
            expected_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/reserves/area_test"
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=" f"input/reserves/{self.area.id}"
            mocker.post(url, status_code=200)
            self.area.create_reserves(series=self.matrix)

            assert mocker.request_history[0].url == expected_url

    def test_create_reserves_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=" f"input/reserves/{self.area.id}"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                MatrixUploadError, match=f"Error uploading matrix for area {self.area.id}: Mocked Server KO"
            ):
                self.area.create_reserves(series=self.matrix)

    def test_create_solar_success(self):
        with requests_mock.Mocker() as mocker:
            expected_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/solar/series/solar_area_test"
            )
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/solar/series/solar_{self.area.id}"
            )
            mocker.post(url, status_code=200)
            self.area.create_solar(series=self.matrix)

            assert mocker.request_history[0].url == expected_url

    def test_create_misc_gen_success(self):
        with requests_mock.Mocker() as mocker:
            expected_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/misc-gen/miscgen-area_test"
            )
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=" f"input/misc-gen/miscgen-{self.area.id}"
            )
            mocker.post(url, status_code=200)
            self.area.create_misc_gen(series=self.matrix)

            assert mocker.request_history[0].url == expected_url
