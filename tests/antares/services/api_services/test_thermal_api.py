import pandas as pd

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import ThermalPropertiesUpdateError, ThermalMatrixDownloadError
from antares.model.area import Area
from antares.model.study import Study
from antares.model.thermal import ThermalCluster, ThermalClusterProperties, ThermalClusterMatrixName
from antares.service.service_factory import ServiceFactory
import requests_mock

import pytest


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
    study = Study("study_test", "870", ServiceFactory(api, study_id))
    area = Area(
        "area-test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )
    thermal = ThermalCluster(ServiceFactory(api, study_id).create_thermal_service(), "area-test", "thermal-test")
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_thermal_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = ThermalClusterProperties(co2=4)
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/"
                f"areas/{self.thermal.area_id}/clusters/thermal/{self.thermal.id}"
            )
            mocker.patch(url, json={"id": "id", "name": "name", **properties.model_dump()}, status_code=200)
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
