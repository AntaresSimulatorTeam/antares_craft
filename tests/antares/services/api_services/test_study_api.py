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

import re

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import (
    AreaCreationError,
    BindingConstraintCreationError,
    LinkCreationError,
    StudyCreationError,
    StudySettingsUpdateError,
)
from antares.model.area import Area, AreaProperties, AreaUi
from antares.model.binding_constraint import BindingConstraint, BindingConstraintProperties
from antares.model.hydro import HydroProperties
from antares.model.link import Link, LinkProperties, LinkUi
from antares.model.settings.general import GeneralParameters
from antares.model.settings.study_settings import StudySettings
from antares.model.study import Study, create_study_api, read_study_api
from antares.service.service_factory import ServiceFactory


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    antares_web_description_msg = "Mocked Server KO"
    study = Study("TestStudy", "880", ServiceFactory(api, study_id))
    area = Area(
        "area_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )

    def test_create_study_test_ok(self) -> None:
        with requests_mock.Mocker() as mocker:
            expected_url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            mocker.post(expected_url, json=self.study_id, status_code=200)
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.get(config_urls, json={}, status_code=200)
            # When
            study = create_study_api("TestStudy", "880", self.api)

            # Then
            assert len(mocker.request_history) == 8
            assert mocker.request_history[0].url == expected_url
            assert isinstance(study, Study)

    def test_create_study_fails(self):
        with requests_mock.Mocker() as mocker:
            url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            study_name = "TestStudy"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                StudyCreationError,
                match=f"Could not create the study {study_name}: {self.antares_web_description_msg}",
            ):
                create_study_api(study_name, "880", self.api)

    def test_update_study_settings_success(self):
        with requests_mock.Mocker() as mocker:
            settings = StudySettings()
            settings.general_parameters = GeneralParameters(mode="Adequacy")
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.put(config_urls, status_code=200)
            mocker.get(config_urls, json={}, status_code=200)
            self.study.update_settings(settings)

    def test_update_study_settings_fails(self):
        with requests_mock.Mocker() as mocker:
            settings = StudySettings()
            settings.general_parameters = GeneralParameters(mode="Adequacy")
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            antares_web_description_msg = "Server KO"
            mocker.put(config_urls, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                StudySettingsUpdateError,
                match=f"Could not update settings for study {self.study_id}: {antares_web_description_msg}",
            ):
                self.study.update_settings(settings)

    def test_create_area_success(self):
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"

            url1 = f"{base_url}/studies/{self.study_id}/areas"
            mocker.post(url1, json={"id": area_name}, status_code=201)
            ui_info = {"ui": {"x": 0, "y": 0, "layers": 0, "color_r": 0, "color_g": 0, "color_b": 0}}
            area_ui = {
                **AreaUi(layerX={"1": 0}, layerY={"1": 0}, layerColor={"1": "0"}).model_dump(by_alias=True),
                **ui_info,
            }
            mocker.get(url1, json={area_name: area_ui}, status_code=201)
            url2 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/properties/form"
            url3 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/hydro/form"
            mocker.put(url2, status_code=201)
            mocker.get(url2, json=AreaProperties().model_dump(), status_code=200)
            mocker.get(url3, json=HydroProperties().model_dump())
            area = self.study.create_area(area_name)
        assert isinstance(area, Area)

    def test_create_area_fails(self):
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                AreaCreationError,
                match=f"Could not create the area {area_name}: {self.antares_web_description_msg}",
            ):
                self.study.create_area(area_name)

    def test_create_link_success(self):
        with requests_mock.Mocker() as mocker:
            base_url = f"https://antares.com/api/v1/studies/{self.study_id}"
            url = f"{base_url}/links"
            mocker.post(url, status_code=200)
            area = Area(
                name="area",
                area_service=self.api,
                storage_service=self.api,
                thermal_service=self.api,
                renewable_service=self.api,
            )
            area_to = Area(
                name="area_to",
                area_service=self.api,
                storage_service=self.api,
                thermal_service=self.api,
                renewable_service=self.api,
            )

            raw_url = f"{base_url}/raw?path=input/links/{area.id}/properties/{area_to.id}"
            json_response = {**LinkProperties().model_dump(by_alias=True), **LinkUi().model_dump(by_alias=True)}
            mocker.get(raw_url, json=json_response, status_code=200)
            link = self.study.create_link(area_from=area, area_to=area_to)
            assert isinstance(link, Link)

    def test_create_link_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/links"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            area_from = Area(
                name="area_from",
                area_service=self.api,
                storage_service=self.api,
                thermal_service=self.api,
                renewable_service=self.api,
            )
            area_to = Area(
                name="area_to",
                area_service=self.api,
                storage_service=self.api,
                thermal_service=self.api,
                renewable_service=self.api,
            )

            with pytest.raises(
                LinkCreationError,
                match=f"Could not create the link {area_from.id} / {area_to.id}: {self.antares_web_description_msg}",
            ):
                self.study.create_link(area_from=area_from, area_to=area_to)

    def test_create_binding_constraint_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            json_response = BindingConstraintProperties().model_dump(mode="json", by_alias=True)
            constraint_name = "bc_1"
            mocker.post(url, json={"id": "id", "name": constraint_name, "terms": [], **json_response}, status_code=201)
            constraint = self.study.create_binding_constraint(name=constraint_name)
            assert isinstance(constraint, BindingConstraint)

    def test_create_binding_constraint_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            constraint_name = "bc_1"

            with pytest.raises(
                BindingConstraintCreationError,
                match=f"Could not create the binding constraint {constraint_name}: {self.antares_web_description_msg}",
            ):
                self.study.create_binding_constraint(name=constraint_name)

    def test_read_study_api(self):
        json_study = {
            "id": "22c52f44-4c2a-407b-862b-490887f93dd8",
            "name": "test_read_areas",
            "version": "880",
        }

        json_area = {
            "zone": {
                "ui": {"x": 0, "y": 0, "color_r": 230, "color_g": 108, "color_b": 44, "layers": "0"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "layerColor": {"0": "230, 108, 44"},
            }
        }

        json_thermal = [
            {
                "id": "therm_un",
                "group": "Gas",
                "name": "therm_un",
                "enabled": "true",
                "unitCount": 1,
                "nominalCapacity": 0,
            }
        ]

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
            "filterSynthesis": ["weekly", "daily", "hourly", "monthly", "annual"],
            "filterByYear": ["weekly", "daily", "hourly", "monthly", "annual"],
            "adequacyPatchMode": "outside",
        }

        config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")

        base_url = "https://antares.com/api/v1"
        url = f"{base_url}/studies/{self.study_id}"
        area_url = f"{url}/areas"
        area_props_url = f"{area_url}/zone/properties/form"
        thermal_url = f"{area_url}/zone/clusters/thermal"
        renewable_url = f"{area_url}/zone/clusters/renewable"
        storage_url = f"{area_url}/zone/storages"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_study)
            mocker.get(config_urls, json={})
            mocker.get(area_url, json=json_area)
            mocker.get(area_props_url, json=json_properties)
            mocker.get(renewable_url, json=json_renewable)
            mocker.get(thermal_url, json=json_thermal)
            mocker.get(storage_url, json=json_st_storage)
            actual_study = read_study_api(self.api, self.study_id)

            expected_study_name = json_study.pop("name")
            expected_study_id = json_study.pop("id")
            expected_study_version = json_study.pop("version")

            expected_study = Study(
                expected_study_name,
                expected_study_version,
                ServiceFactory(self.api, expected_study_id, expected_study_name),
                None,
            )

            assert actual_study.name == expected_study.name
            assert actual_study.version == expected_study.version
            assert actual_study.service.study_id == expected_study.service.study_id
