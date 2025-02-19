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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    AreaPropertiesUpdateError,
    AreasRetrievalError,
    AreaUiUpdateError,
    RenewableCreationError,
    STStorageCreationError,
    ThermalCreationError,
)
from antares.craft.model.area import Area, AreaPropertiesUpdate, AreaUi
from antares.craft.model.hydro import Hydro, HydroProperties, HydroPropertiesUpdate
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage
from antares.craft.model.study import Study
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.area import AreaPropertiesAPI
from antares.craft.service.api_services.models.hydro import HydroPropertiesAPI
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.models.st_storage import STStoragePropertiesAPI
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.services.area import AreaApiService


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    services = create_api_services(api, study_id)
    area_service = services.area_service
    st_storage_service = services.short_term_storage_service
    thermal_service = services.thermal_service
    renewable_service = services.renewable_service
    hydro_service = services.hydro_service
    area = Area("area_test", area_service, st_storage_service, thermal_service, renewable_service, hydro_service)

    area_api = AreaApiService(
        api,
        "248bbb99-c909-47b7-b239-01f6f6ae7de7",
        st_storage_service,
        thermal_service,
        renewable_service,
        hydro_service,
    )
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[1]])
    study = Study("TestStudy", "880", services)

    def test_update_area_properties_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/properties/form"
            properties = AreaPropertiesUpdate(energy_cost_spilled=1)
            api_properties = AreaPropertiesAPI.from_user_model(properties)
            mocker.put(url, status_code=200)
            mocker.get(url, json=api_properties.model_dump(mode="json", by_alias=True), status_code=200)
            self.area.update_properties(properties=properties)
            assert self.area.properties.energy_cost_spilled == 1

    def test_update_area_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/properties/form"
            properties = AreaPropertiesUpdate(energy_cost_unsupplied=100)
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
            json_response = ThermalClusterPropertiesAPI().model_dump(mode="json", by_alias=True)
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
            json_response = RenewableClusterPropertiesAPI().model_dump(mode="json", by_alias=True)
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
            json_response = STStoragePropertiesAPI().model_dump(mode="json", by_alias=True)
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
        base_url = f"{self.api.api_host}/api/v1"
        with requests_mock.Mocker() as mocker:
            url = f"{base_url}/studies/{self.study_id}/areas/{self.area.id}/clusters/thermal"
            cluster_name = "cluster_test"
            creation_response = {"name": cluster_name, "id": cluster_name, "group": "nuclear"}
            mocker.post(url, json=creation_response, status_code=200)

            raw_url = f"{base_url}/studies/{self.study_id}/raw"
            mocker.post(raw_url, json={}, status_code=200)

            thermal_cluster = self.area.create_thermal_cluster(
                thermal_name=cluster_name,
                properties=ThermalClusterProperties(),
                prepro=self.matrix,
                series=self.matrix,
                fuel_cost=self.matrix,
            )
            # Asserts 4 commands were created
            # 1 for the properties and 1 for each matrix we filled
            assert len(mocker.request_history) == 4
            assert isinstance(thermal_cluster, ThermalCluster)

    def test_create_hydro_success(self):
        url_hydro_form = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/hydro/form"
        body = {"reservoir": True}
        with requests_mock.Mocker() as mocker:
            mocker.put(url_hydro_form, status_code=200)
            mocker.get(url_hydro_form, json=body, status_code=200)
            assert self.area.hydro.properties.reservoir is False
            self.area.hydro.update_properties(HydroPropertiesUpdate(reservoir=True))
            assert self.area.hydro.properties.reservoir is True

    def test_read_areas_success(self):
        area_id = "zone"
        url = f"https://antares.com/api/v1/studies/{self.study_id}/areas"
        ui_url = url + "?ui=true"
        url_thermal = url + f"/{area_id}/clusters/thermal"
        url_renewable = url + f"/{area_id}/clusters/renewable"
        url_st_storage = url + f"/{area_id}/storages"
        url_properties_form = url + f"/{area_id}/properties/form"
        hydro_url = url + f"/{area_id}/hydro/form"

        json_ui = {
            area_id: {
                "ui": {"x": 0, "y": 0, "color_r": 230, "color_g": 108, "color_b": 44, "layers": "0"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "layerColor": {"0": "230, 108, 44"},
            }
        }
        json_thermal = [
            {
                "id": "therm_un",
                "group": "gas",
                "name": "therm_un",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
            }
        ]
        json_renewable = [
            {
                "id": "test_renouvelable",
                "group": "solar thermal",
                "name": "test_renouvelable",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
                "tsInterpretation": "power-generation",
            }
        ]
        json_st_storage = [
            {
                "id": "test_storage",
                "group": "Pondage",
                "name": "test_storage",
                "injectionNominalCapacity": 0,
                "withdrawalNominalCapacity": 0,
                "reservoirCapacity": 0,
                "efficiency": 1,
                "initialLevel": 0.5,
                "initialLevelOptim": "false",
                "enabled": "true",
            }
        ]
        json_properties = {
            "energyCostUnsupplied": 0,
            "energyCostSpilled": 0,
            "nonDispatchPower": "true",
            "dispatchHydroPower": "true",
            "otherDispatchPower": "true",
            "filterSynthesis": ["daily", "monthly", "weekly", "hourly", "annual"],
            "filterByYear": ["daily", "monthly", "weekly", "hourly", "annual"],
            "adequacyPatchMode": "outside",
        }

        hydro_properties = HydroProperties(reservoir_capacity=4.5)

        with requests_mock.Mocker() as mocker:
            mocker.get(ui_url, json=json_ui)
            mocker.get(url_thermal, json=json_thermal)
            mocker.get(url_renewable, json=json_renewable)
            mocker.get(url_st_storage, json=json_st_storage)
            mocker.get(url_properties_form, json=json_properties)
            mocker.get(hydro_url, json={"reservoir_capacity": 4.5})

            actual_area_list = self.study.read_areas()
            area_ui = self.area_api.craft_ui(url + "?type=AREA&ui=true", "zone")

            thermal_ = json_thermal[0]
            thermal_id = thermal_.pop("id")
            thermal_name = thermal_.pop("name")

            renewable_ = json_renewable[0]
            renewable_id = renewable_.pop("id")
            renewable_name = renewable_.pop("name")

            storage_ = json_st_storage[0]
            storage_id = storage_.pop("id")
            storage_name = storage_.pop("name")

            thermal_props = ThermalClusterPropertiesAPI(**thermal_).to_user_model()
            thermal_cluster = ThermalCluster(self.area_api.thermal_service, thermal_id, thermal_name, thermal_props)
            renewable_props = RenewableClusterPropertiesAPI(**renewable_).to_user_model()
            renewable_cluster = RenewableCluster(
                self.area_api.renewable_service, renewable_id, renewable_name, renewable_props
            )
            storage_props = STStoragePropertiesAPI(**storage_).to_user_model()
            st_storage = STStorage(self.area_api.storage_service, storage_id, storage_name, storage_props)

            hydro = Hydro(self.area_api.hydro_service, area_id, hydro_properties)

            expected_area = Area(
                area_id,
                self.area_api,
                self.area_api.storage_service,
                self.area_api.thermal_service,
                self.area_api.renewable_service,
                self.area_api.hydro_service,
                thermals={thermal_id: thermal_cluster},
                renewables={renewable_id: renewable_cluster},
                st_storages={storage_id: st_storage},
                hydro=hydro,
                properties=AreaPropertiesAPI.model_validate(json_properties).to_user_model(),
                ui=area_ui,
            )

            assert len(actual_area_list) == 1
            actual_area = actual_area_list[0]
            assert actual_area.id == expected_area.id
            assert actual_area.name == expected_area.name
            actual_thermals = actual_area.get_thermals()
            actual_renewables = actual_area.get_renewables()
            actual_storages = actual_area.get_st_storages()
            assert len(actual_renewables) == len(expected_area.get_renewables())
            assert len(actual_storages) == len(expected_area.get_st_storages())
            assert len(actual_thermals) == len(expected_area.get_thermals())
            assert actual_thermals[thermal_id].name == expected_area.get_thermals()[thermal_id].name
            assert actual_renewables[renewable_id].name == expected_area.get_renewables()[renewable_id].name
            assert actual_storages[storage_id].name == expected_area.get_st_storages()[storage_id].name
            assert actual_area.hydro.properties == hydro_properties

    def test_read_areas_fail(self):
        with requests_mock.Mocker() as mocker:
            url_areas = f"https://antares.com/api/v1/studies/{self.study_id}/areas"
            mocker.get(url_areas, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                AreasRetrievalError,
                match=f"Could not retrieve the areas from the study {self.study_id} : "
                + self.antares_web_description_msg,
            ):
                self.study.read_areas()

    def test_read_hydro(self):
        json_hydro = {
            "interDailyBreakdown": 1,
            "intraDailyModulation": 24,
            "interMonthlyBreakdown": 1,
            "reservoir": "false",
            "reservoirCapacity": 0,
            "followLoad": "true",
            "useWater": "false",
            "hardBounds": "false",
            "initializeReservoirDate": 0,
            "useHeuristic": "true",
            "powerToLevel": "false",
            "useLeeway": "false",
            "leewayLow": 1,
            "leewayUp": 1,
            "pumpingEfficiency": 1,
        }
        url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area.id}/hydro/form"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_hydro)
            hydro_props = HydroPropertiesAPI(**json_hydro).to_user_model()

            actual_hydro = Hydro(self.api, self.area.id, hydro_props)
            assert actual_hydro.properties == self.area.hydro.read_properties()

    def test_read_renewables_empty(self):
        area = self.area
        url_renewable = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{area.id}/clusters/renewable"

        with requests_mock.Mocker() as mocker:
            mocker.get(
                url_renewable,
                status_code=404,
                json={"description": "'renewables' not a child of Input", "exception": "ChildNotFoundError"},
            )

            actual_renewables = area.read_renewables()

            assert actual_renewables == []
