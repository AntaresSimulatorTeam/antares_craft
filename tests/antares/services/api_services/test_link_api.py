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
    LinkDownloadError,
    LinkPropertiesUpdateError,
    LinksRetrievalError,
    LinkUiUpdateError,
    LinkUploadError,
)
from antares.craft.model.area import Area
from antares.craft.model.commons import FilterOption
from antares.craft.model.link import Link, LinkProperties, LinkUi
from antares.craft.model.study import Study
from antares.craft.service.api_services.factory import ApiServiceFactory


@pytest.fixture()
def expected_link():
    area_from_name = "zone1 auto"
    area_to_name = "zone4auto"
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    factory = ApiServiceFactory(api, study_id)
    link_service = factory.create_link_service()
    properties = {
        "hurdles-cost": False,
        "loop-flow": False,
        "use-phase-shifter": False,
        "transmission-capacities": "enabled",
        "asset-type": "ac",
        "display-comments": True,
        "colorr": 112,
        "colorb": 112,
        "colorg": 112,
        "linkWidth": 1,
        "linkStyle": "plain",
        "filter-synthesis": set("hourly, daily, weekly, monthly, annual".split(", ")),
        "filter-year-by-year": set("hourly, daily, weekly, monthly, annual".split(", ")),
    }
    color_r = properties.pop("colorr")
    color_b = properties.pop("colorb")
    color_g = properties.pop("colorg")
    link_width = properties.pop("linkWidth")
    link_style = properties.pop("linkStyle")
    link_properties = LinkProperties(**properties)
    link_ui = LinkUi(colorg=color_g, colorb=color_b, colorr=color_r, link_style=link_style, link_width=link_width)
    return Link(area_from_name, area_to_name, link_service, link_properties, link_ui)


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    factory = ApiServiceFactory(api, study_id)
    study = Study("study_test", "870", factory)
    area_from = Area(
        name="area_from",
        area_service=api,
        storage_service=api,
        thermal_service=api,
        renewable_service=api,
        hydro_service=api,
    )
    area_to = Area(
        name="area_to",
        area_service=api,
        storage_service=api,
        thermal_service=api,
        renewable_service=api,
        hydro_service=api,
    )
    antares_web_description_msg = "Mocked Server KO"
    link = Link(area_from.id, area_to.id, factory.create_link_service())
    matrix = pd.DataFrame(data=[[0]])

    def test_update_links_properties_success(self):
        with requests_mock.Mocker() as mocker:
            properties = LinkProperties()
            properties.filter_synthesis = {FilterOption.DAILY}
            properties.filter_year_by_year = {FilterOption.DAILY}
            ui = LinkUi()
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/links/"
                f"{self.area_from.id}/properties/{self.area_to.id}"
            )
            mocker.post(raw_url, status_code=200)
            mocker.get(
                raw_url,
                json={**ui.model_dump(by_alias=True), **properties.model_dump(mode="json", by_alias=True)},
                status_code=200,
            )

            self.link.update_properties(properties)

    def test_update_links_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            properties = LinkProperties()
            properties.filter_synthesis = {FilterOption.DAILY}
            properties.filter_year_by_year = {FilterOption.DAILY}
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/links/"
                f"{self.area_from.id}/properties/{self.area_to.id}"
            )
            antares_web_description_msg = "Server KO"
            mocker.get(raw_url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkPropertiesUpdateError,
                match=f"Could not update properties for link {self.link.id}: {antares_web_description_msg}",
            ):
                self.link.update_properties(properties)

    def test_update_links_ui_success(self):
        with requests_mock.Mocker() as mocker:
            properties = LinkProperties()
            ui = LinkUi()
            ui.link_width = 12
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/links/{self.area_from.id}"
                f"/properties/{self.area_to.id}"
            )
            mocker.post(raw_url, status_code=200)
            mocker.get(
                raw_url, json={**ui.model_dump(by_alias=True), **properties.model_dump(by_alias=True)}, status_code=200
            )

            self.link.update_ui(ui)

    def test_update_links_ui_fails(self):
        with requests_mock.Mocker() as mocker:
            ui = LinkUi()
            ui.link_width = 12
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=input/links/{self.area_from.id}"
                f"/properties/{self.area_to.id}"
            )
            antares_web_description_msg = "Server KO"
            mocker.get(raw_url, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                LinkUiUpdateError,
                match=f"Could not update ui for link {self.link.id}: {antares_web_description_msg}",
            ):
                self.link.update_ui(ui)

    def test_create_parameters_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/{self.area_to.id}_parameters"
            )

            mocker.post(raw_url, status_code=200)

            self.link.create_parameters(self.matrix)

    def test_create_parameters_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/{self.area_to.id}_parameters"
            )

            antares_web_description_msg = "Server KO"
            mocker.post(raw_url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkUploadError,
                match=f"Error uploading parameters matrix for link {self.link.area_from_id}/{self.link.area_to_id}",
            ):
                self.link.create_parameters(self.matrix)

    def test_create_direct_capacity_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_direct"
            )

            mocker.post(raw_url, status_code=200)

            self.link.create_capacity_direct(self.matrix)

    def test_create_direct_capacity_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_direct"
            )

            antares_web_description_msg = "Server KO"
            mocker.post(raw_url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkUploadError,
                match=f"Error uploading directcapacity matrix for link {self.link.area_from_id}/{self.link.area_to_id}",
            ):
                self.link.create_capacity_direct(self.matrix)

    def test_create_indirect_capacity_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_indirect"
            )

            mocker.post(raw_url, status_code=200)

            self.link.create_capacity_indirect(self.matrix)

    def test_create_indirect_capacity_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_indirect"
            )

            mocker.post(raw_url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkUploadError,
                match=f"Error uploading indirectcapacity matrix for link {self.link.area_from_id}/{self.link.area_to_id}",
            ):
                self.link.create_capacity_indirect(self.matrix)

    def test_get_parameters_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/{self.area_to.id}_parameters"
            )
            mocker.get(raw_url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)

            matrix = self.link.get_parameters()
            assert matrix.equals(self.matrix)

    def test_get_parameters_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/{self.area_to.id}_parameters"
            )

            mocker.get(raw_url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkDownloadError,
                match=f"Could not download parameters matrix for link {self.area_from.id}/{self.area_to.id}",
            ):
                self.link.get_parameters()

    def test_get_indirect_capacity_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_indirect"
            )
            mocker.get(raw_url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)

            matrix = self.link.get_capacity_indirect()
            assert matrix.equals(self.matrix)

    def test_get_indirect_capacity_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_indirect"
            )

            mocker.get(raw_url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkDownloadError,
                match=f"Could not download indirectcapacity matrix for link {self.area_from.id}/{self.area_to.id}",
            ):
                self.link.get_capacity_indirect()

    def test_get_direct_capacity_success(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_direct"
            )
            mocker.get(raw_url, json={"data": [[0]], "index": [0], "columns": [0]}, status_code=200)

            matrix = self.link.get_capacity_direct()
            assert matrix.equals(self.matrix)

    def test_get_direct_capacity_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/raw?path="
                f"input/links/{self.area_from.id}/capacities/{self.area_to.id}_direct"
            )

            mocker.get(raw_url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinkDownloadError,
                match=f"Could not download directcapacity matrix for link {self.area_from.id}/{self.area_to.id}",
            ):
                self.link.get_capacity_direct()

    def test_read_links(self, expected_link):
        url_read_links = f"https://antares.com/api/v1/studies/{self.study_id}/links"

        json_links = [
            {
                "hurdlesCost": False,
                "loopFlow": False,
                "usePhaseShifter": False,
                "transmissionCapacities": "enabled",
                "assetType": "ac",
                "displayComments": True,
                "colorr": 112,
                "colorb": 112,
                "colorg": 112,
                "linkWidth": 1,
                "linkStyle": "plain",
                "filterSynthesis": "hourly, daily, weekly, monthly, annual",
                "filterYearByYear": "hourly, daily, weekly, monthly, annual",
                "area1": "zone1 auto",
                "area2": "zone4auto",
            }
        ]

        with requests_mock.Mocker() as mocker:
            mocker.get(url_read_links, json=json_links)
            actual_link_list = self.study.read_links()
            assert len(actual_link_list) == 1
            actual_link = actual_link_list[0]
            assert expected_link.id == actual_link.id
            assert expected_link.properties == actual_link.properties
            assert expected_link.ui == actual_link.ui

    def test_read_links_fail(self):
        with requests_mock.Mocker() as mocker:
            raw_url = f"https://antares.com/api/v1/studies/{self.study_id}/links"
            mocker.get(raw_url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                LinksRetrievalError,
                match=f"Could not retrieve links from study {self.study_id} : {self.antares_web_description_msg}",
            ):
                self.study.read_links()
