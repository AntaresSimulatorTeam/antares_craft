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
from antares.exceptions.exceptions import (
    AreaDeletionError,
    LinkDeletionError,
    ThermalDeletionError,
    RenewableDeletionError,
    STStorageDeletionError,
    BindingConstraintDeletionError,
    ConstraintTermDeletionError,
)
from antares.model.area import Area
from antares.model.binding_constraint import BindingConstraint
from antares.model.link import Link
from antares.model.renewable import RenewableCluster
from antares.model.st_storage import STStorage
from antares.model.thermal import ThermalCluster
from antares.service.api_services.area_api import AreaApiService
from antares.service.api_services.binding_constraint_api import BindingConstraintApiService
from antares.service.api_services.link_api import LinkApiService
from antares.service.api_services.renewable_api import RenewableApiService
from antares.service.api_services.st_storage_api import ShortTermStorageApiService
from antares.service.api_services.study_api import StudyApiService
from antares.service.api_services.thermal_api import ThermalApiService


class TestDeleteAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    study_service = StudyApiService(api, study_id)
    area_service = AreaApiService(api, study_id)
    thermal_service = ThermalApiService(api, study_id)
    renewable_service = RenewableApiService(api, study_id)
    st_storage_service = ShortTermStorageApiService(api, study_id)
    area_fr = Area("fr", area_service, st_storage_service, thermal_service, renewable_service)
    area_be = Area("be", area_service, st_storage_service, thermal_service, renewable_service)
    link_service = LinkApiService(api, study_id)
    constraint_service = BindingConstraintApiService(api, study_id)
    antares_web_description_msg = "Mocked Server KO"

    def test_delete_area_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}"
            mocker.delete(url, status_code=200)
            self.area_service.delete_area(area=self.area_fr)

    def test_delete_area_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                AreaDeletionError,
                match=f"Could not delete the area {self.area_fr.id}: {self.antares_web_description_msg}",
            ):
                self.area_service.delete_area(area=self.area_fr)

    def test_delete_link_success(self):
        with requests_mock.Mocker() as mocker:
            link = Link(self.area_be, self.area_fr, self.link_service)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/links/{self.area_be.id}/{self.area_fr.id}"
            mocker.delete(url, status_code=200)
            self.link_service.delete_link(link)

    def test_delete_link_fails(self):
        with requests_mock.Mocker() as mocker:
            link = Link(self.area_fr, self.area_be, self.link_service)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/links/{self.area_fr.id}/{self.area_be.id}"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                LinkDeletionError,
                match=f"Could not delete the link {self.area_fr.id} / {self.area_be.id}: {self.antares_web_description_msg}",
            ):
                self.link_service.delete_link(link)

    def test_delete_thermal_success(self):
        with requests_mock.Mocker() as mocker:
            cluster = ThermalCluster(self.thermal_service, self.area_fr.id, "gaz_cluster")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/clusters/thermal"
            mocker.delete(url, status_code=200)
            self.area_service.delete_thermal_clusters(self.area_fr, [cluster])

    def test_delete_thermal_fails(self):
        with requests_mock.Mocker() as mocker:
            cluster1 = ThermalCluster(self.thermal_service, self.area_fr.id, "gaz_cluster")
            cluster2 = ThermalCluster(self.thermal_service, self.area_fr.id, "gaz_cluster_2")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/clusters/thermal"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ThermalDeletionError,
                match=f"Could not delete the following thermal clusters: gaz_cluster, gaz_cluster_2 inside area fr: {self.antares_web_description_msg}",
            ):
                self.area_service.delete_thermal_clusters(self.area_fr, [cluster1, cluster2])

    def test_delete_renewable_success(self):
        with requests_mock.Mocker() as mocker:
            cluster = RenewableCluster(self.renewable_service, self.area_fr.id, "gaz_cluster")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/clusters/renewable"
            mocker.delete(url, status_code=200)
            self.area_service.delete_renewable_clusters(self.area_fr, [cluster])

    def test_delete_renewable_fails(self):
        with requests_mock.Mocker() as mocker:
            cluster = RenewableCluster(self.renewable_service, self.area_fr.id, "gaz_cluster")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/clusters/renewable"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                RenewableDeletionError,
                match=f"Could not delete the following renewable clusters: gaz_cluster inside area fr: {self.antares_web_description_msg}",
            ):
                self.area_service.delete_renewable_clusters(self.area_fr, [cluster])

    def test_delete_st_storage_success(self):
        with requests_mock.Mocker() as mocker:
            storage = STStorage(self.st_storage_service, self.area_fr.id, "battery_fr")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/storages"
            mocker.delete(url, status_code=200)
            self.area_service.delete_st_storages(self.area_fr, [storage])

    def test_delete_st_storage_fails(self):
        with requests_mock.Mocker() as mocker:
            storage = STStorage(self.st_storage_service, self.area_fr.id, "battery_fr")
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/{self.area_fr.id}/storages"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                STStorageDeletionError,
                match=f"Could not delete the following short term storages: battery_fr inside area fr: {self.antares_web_description_msg}",
            ):
                self.area_service.delete_st_storages(self.area_fr, [storage])

    def test_delete_binding_constraint_success(self):
        with requests_mock.Mocker() as mocker:
            constraint_id = "bc_1"
            constraint = BindingConstraint(constraint_id, self.constraint_service)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint_id}"
            mocker.delete(url, status_code=200)
            self.study_service.delete_binding_constraint(constraint)

    def test_delete_binding_constraint_fails(self):
        with requests_mock.Mocker() as mocker:
            constraint_id = "bc_1"
            constraint = BindingConstraint(constraint_id, self.constraint_service)
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint_id}"
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                BindingConstraintDeletionError,
                match=f"Could not delete the binding constraint {constraint_id}: {self.antares_web_description_msg}",
            ):
                self.study_service.delete_binding_constraint(constraint)

    def test_delete_constraint_terms_success(self):
        with requests_mock.Mocker() as mocker:
            constraint_id = "bc_1"
            term_id = "term_1"
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint_id}/term/{term_id}"
            )
            mocker.delete(url, status_code=200)
            self.constraint_service.delete_binding_constraint_term(constraint_id, term_id)

    def test_delete_constraint_terms_fails(self):
        with requests_mock.Mocker() as mocker:
            constraint_id = "bc_1"
            term_id = "term_1"
            url = (
                f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint_id}/term/{term_id}"
            )
            mocker.delete(url, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                ConstraintTermDeletionError,
                match=f"Could not delete the term {term_id} of the binding constraint {constraint_id}: {self.antares_web_description_msg}",
            ):
                self.constraint_service.delete_binding_constraint_term(constraint_id, term_id)