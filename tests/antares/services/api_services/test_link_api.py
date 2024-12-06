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

from antares.api_conf.api_conf import APIconf
from antares.exceptions.exceptions import LinkPropertiesUpdateError, LinkUiUpdateError
from antares.model.area import Area
from antares.model.commons import FilterOption
from antares.model.link import Link, LinkProperties, LinkUi
from antares.model.study import Study
from antares.service.service_factory import ServiceFactory


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    study = Study("study_test", "870", ServiceFactory(api, study_id))
    area_from = Area(
        name="area_from", area_service=api, storage_service=api, thermal_service=api, renewable_service=api
    )
    area_to = Area(name="area_to", area_service=api, storage_service=api, thermal_service=api, renewable_service=api)
    antares_web_description_msg = "Mocked Server KO"
    link = Link(area_from.id, area_to.id, ServiceFactory(api, study_id).create_link_service())

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
        pass

    def test_create_parameters_fail(self):
        pass

    def test_create_direct_capacity_success(self):
        pass

    def test_create_direct_capacity_fail(self):
        pass

    def test_create_indirect_capacity_success(self):
        pass

    def test_create_indirect_capacity_fail(self):
        pass

    def test_get_parameters(self):
        pass

    def test_get_indirect_capacity(self):
        pass

    def test_get_direct_capacity(self):
        pass
