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
    ConstraintMatrixDownloadError,
    ConstraintsPropertiesUpdateError,
    ConstraintTermsSettingError,
)
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintMatrixName,
    ConstraintTerm,
    LinkData,
)
from antares.craft.model.study import Study
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI

fixture_type = list[tuple[str, ConstraintMatrixName, str, list[list[int]]]]


@pytest.fixture
def constraint_set() -> fixture_type:
    params = [
        ("get_less_term_matrix", ConstraintMatrixName.LESS_TERM, "input/bindingconstraints/bc_test_lt", [[0]]),
        ("get_greater_term_matrix", ConstraintMatrixName.GREATER_TERM, "input/bindingconstraints/bc_test_gt", [[0]]),
        ("get_equal_term_matrix", ConstraintMatrixName.EQUAL_TERM, "input/bindingconstraints/bc_test_eq", [[0]]),
    ]
    return params


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    services = create_api_services(api, study_id)
    study = Study("study_test", "880", services)
    area = Area(
        "study_test",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])
    study_url = f"https://antares.com/api/v1/studies/{study_id}"

    def test_update_binding_constraint_properties_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            update_properties = BindingConstraintPropertiesUpdate(enabled=False)
            creation_properties = BindingConstraintProperties(enabled=False)
            api_properties = BindingConstraintPropertiesAPI.from_user_model(creation_properties)
            constraint = BindingConstraint("bc_1", self.services.bc_service)
            url = f"{self.study_url}/table-mode/binding-constraints"
            mocker.put(
                url,
                json={"bc_1": api_properties.model_dump(mode="json")},
                status_code=200,
            )
            constraint.update_properties(properties=update_properties)
            assert constraint.properties == BindingConstraintProperties(enabled=False)

    def test_update_binding_constraint_properties_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            update_properties = BindingConstraintPropertiesUpdate(enabled=False)
            constraint = BindingConstraint("bc_1", self.services.bc_service)
            url = f"{self.study_url}/table-mode/binding-constraints"
            antares_web_description_msg = "Server KO"
            mocker.put(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ConstraintsPropertiesUpdateError,
                match=f"Could not update binding constraints properties from study '{self.study_id}': {antares_web_description_msg}",
            ):
                constraint.update_properties(properties=update_properties)

    def test_get_constraint_matrix_success(self, constraint_set: fixture_type) -> None:
        constraint = BindingConstraint("bc_test", self.services.bc_service)
        for matrix_method, enum_value, path, expected_matrix in constraint_set:
            with requests_mock.Mocker() as mocker:
                url = f"{self.study_url}/raw?path={path}"
                mocker.get(url, json={"data": expected_matrix, "index": [0], "columns": [0]}, status_code=200)
                constraint_matrix = getattr(constraint, matrix_method)()
            assert constraint_matrix.equals(self.matrix)

    def test_get_constraint_matrix_fails(self, constraint_set: fixture_type) -> None:
        constraint = BindingConstraint("bc_test", self.services.bc_service)
        for matrix_method, enum_value, path, _ in constraint_set:
            with requests_mock.Mocker() as mocker:
                url = f"{self.study_url}/raw?path={path}"
                mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
                with pytest.raises(
                    ConstraintMatrixDownloadError,
                    match=f"Could not download matrix {enum_value.value} for binding constraint '{constraint.name}':",
                ):
                    getattr(constraint, matrix_method)()

    def test_set_binding_constraint_terms_success(self) -> None:
        existing_term_1 = ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=4, offset=3)
        existing_term_2 = ConstraintTerm(data=LinkData(area1="be", area2="de"), weight=1, offset=8)
        constraint = BindingConstraint("bc_1", self.services.bc_service, None, [existing_term_1, existing_term_2])
        url = f"{self.study_url}/bindingconstraints/{constraint.id}"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=200)

            constraint.set_terms([existing_term_1, existing_term_2])

            terms = constraint.get_terms()
            assert list(terms.values()) == [existing_term_1, existing_term_2]

            mocker.put(url, status_code=200)
            new_term_1 = ConstraintTerm(data=LinkData(area1="ita", area2="fr"), weight=9, offset=7)
            new_term_2 = ConstraintTerm(data=LinkData(area1="be", area2="en"), weight=10, offset=4)
            constraint.set_terms([new_term_1, new_term_2])

            terms = constraint.get_terms()
            assert list(terms.values()) == [new_term_1, new_term_2]

    def test_set_binding_constraint_terms_fail_setting(self) -> None:
        constraint = BindingConstraint("bc_1", self.services.bc_service, None, [])
        url = f"{self.study_url}/bindingconstraints/{constraint.id}"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=422)

            with pytest.raises(
                ConstraintTermsSettingError,
                match=f"Could not set binding constraint {constraint.name} terms from the study {self.study_id} : "
                f"{self.antares_web_description_msg}",
            ):
                constraint.set_terms([])
