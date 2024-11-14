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

import json

import numpy as np
import pandas as pd

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import (
    AreaPropertiesUpdateError,
    AreaUiUpdateError,
    LoadMatrixDownloadError,
    LoadMatrixUploadError,
    MatrixUploadError,
    RenewableCreationError,
    STStorageCreationError,
    ThermalCreationError,
)
from antares.model.area import Area, AreaProperties, AreaUi
from antares.model.hydro import Hydro, HydroMatrixName, HydroProperties
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.model.st_storage import STStorage, STStorageProperties
from antares.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.service.api_services.area_api import AreaApiService
from antares.service.service_factory import ServiceFactory


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
    area_api = AreaApiService(api, "248bbb99-c909-47b7-b239-01f6f6ae7de7")
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
            json_response = ThermalClusterProperties().model_dump(mode="json", by_alias=True)
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
            json_response = RenewableClusterProperties().model_dump(mode="json", by_alias=True)
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
            json_response = STStorageProperties().model_dump(mode="json", by_alias=True)
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
        json_for_post = HydroProperties().model_dump(mode="json", by_alias=True)
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

    def test_read_areas(self):
        #-web - recette.rte - france
        study_id_test="248bbb99-c909-47b7-b239-01f6f6ae7de7"
        url = f"https://antares.com/api/v1/studies/{study_id_test}/areas"
        ui_url = url + "?ui=true"
        url_thermal = url + "/zone/clusters/thermal"
        url_renewable = url + "/zone/clusters/renewable"
        url_st_storage = url + "/zone/storages"
        url_properties_form = url + "/zone/properties/form"

        json_ui = json.loads("""{"zone":{"ui":{"x":0,"y":0,"color_r":230,"color_g":108,"color_b":44,"layers":"0"},"layerX":{"0":0},"layerY":{"0":0},"layerColor":{"0":"230, 108, 44"}}}""")
        json_thermal = [json.loads("""{"id":"therm_un","group":"Gas","name":"therm_un","enabled":true,"unitCount":1,"nominalCapacity":0,"genTs":"use global","minStablePower":0,"minUpTime":1,"minDownTime":1,"mustRun":false,"spinning":0,"volatilityForced":0,"volatilityPlanned":0,"lawForced":"uniform","lawPlanned":"uniform","marginalCost":0,"spreadCost":0,"fixedCost":0,"startupCost":0,"marketBidCost":0,"co2":0,"nh3":0,"so2":0,"nox":0,"pm25":0,"pm5":0,"pm10":0,"nmvoc":0,"op1":0,"op2":0,"op3":0,"op4":0,"op5":0,"costGeneration":"SetManually","efficiency":100,"variableOMCost":0}""")]
        json_renewable = [json.loads("""{"id":"test_renouvelable","group":"Solar Thermal","name":"test_renouvelable","enabled":"true","unitCount":1,"nominalCapacity":0,"tsInterpretation":"power-generation"}""")]
        json_st_storage = [json.loads("""{"id":"test_storage","group":"Pondage","name":"test_storage","injectionNominalCapacity":0,"withdrawalNominalCapacity":0,"reservoirCapacity":0,"efficiency":1,"initialLevel":0.5,"initialLevelOptim":false,"enabled":"true"}""")]
        json_properties = json.loads("""{"energyCostUnsupplied":0,"energyCostSpilled":0,"nonDispatchPower":true,"dispatchHydroPower":true,"otherDispatchPower":true,"filterSynthesis":["daily","monthly","weekly","hourly","annual"],"filterByYear":["daily","monthly","weekly","hourly","annual"],"adequacyPatchMode":"outside"}""")

        with requests_mock.Mocker() as mocker:

            mocker.get(ui_url, json=json_ui)
            mocker.get(url_thermal, json=json_thermal)
            mocker.get(url_renewable, json=json_renewable)
            mocker.get(url_st_storage, json=json_st_storage)
            mocker.get(url_properties_form, json=json_properties)

            area_api = AreaApiService(self.api, study_id_test)
            area_list = area_api.read_areas()
            area_ui = area_api.craft_ui(url + "?type=AREA&ui=true", "zone")

            thermal_id = json_thermal[0].pop("id")
            thermal_name = json_thermal[0].pop("name")
            renewable_id = json_renewable[0].pop("id")
            renewable_name = json_renewable[0].pop("name")
            storage_id = json_st_storage[0].pop("id")
            storage_name = json_st_storage[0].pop("name")

            thermal_props = ThermalClusterProperties(**json_thermal[0])
            thermal_cluster = ThermalCluster(self.area_api.thermal_service, thermal_id, thermal_name, thermal_props)
            renewable_props = RenewableClusterProperties(**json_renewable[0])
            renewable_cluster = RenewableCluster(self.area_api.renewable_service, renewable_id, renewable_name, renewable_props)
            storage_props = STStorageProperties(**json_st_storage[0])
            st_storage = STStorage(self.area_api.storage_service, storage_id, storage_name, storage_props)

            area_test = Area("zone",
                    self.area_api, self.area_api.storage_service,
                    self.area_api.thermal_service, self.area_api.renewable_service,
                    thermals={thermal_id:thermal_cluster}, renewables={renewable_id:renewable_cluster},
                    st_storages={storage_id:st_storage}, properties=json_properties)

            area_test_list = []
            area_test_list.append(area_test)

            assert len(area_list) == len(area_test_list)
            assert area_list[0].id == area_test_list[0].id
            assert area_list[0].name == area_test_list[0].name
            assert len(area_list[0].get_renewables()) == len(area_test_list[0].get_renewables())
            assert len(area_list[0].get_st_storages()) == len(area_test_list[0].get_st_storages())
            assert len(area_list[0].get_thermals()) == len(area_test_list[0].get_thermals())
            assert area_list[0].get_thermals().get(thermal_id).name == area_test_list[0].get_thermals().get(thermal_id).name
            assert area_list[0].get_renewables().get(renewable_id).name == area_test_list[0].get_renewables().get(renewable_id).name
            assert area_list[0].get_st_storages().get(storage_id).name == area_test_list[0].get_st_storages().get(storage_id).name
