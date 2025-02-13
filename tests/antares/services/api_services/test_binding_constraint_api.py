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
from antares.craft.exceptions.exceptions import ConstraintMatrixDownloadError, ConstraintPropertiesUpdateError
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintMatrixName,
    ConstraintTerm,
    ConstraintTermUpdate,
    LinkData,
)
from antares.craft.model.study import Study
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.service_factory import ServiceFactory


@pytest.fixture
def constraint_set():
    params = [
        ("get_less_term_matrix", ConstraintMatrixName.LESS_TERM, "input/bindingconstraints/bc_test_lt", [[0]]),
        ("get_greater_term_matrix", ConstraintMatrixName.GREATER_TERM, "input/bindingconstraints/bc_test_gt", [[0]]),
        ("get_equal_term_matrix", ConstraintMatrixName.EQUAL_TERM, "input/bindingconstraints/bc_test_eq", [[0]]),
    ]
    return params


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    study = Study("study_test", "870", ServiceFactory(api, study_id))
    area = Area(
        "study_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
        ServiceFactory(api, study_id).create_hydro_service(),
    )
    antares_web_description_msg = "Mocked Server KO"
    matrix = pd.DataFrame(data=[[0]])

    def test_update_binding_constraint_properties_success(self):
        with requests_mock.Mocker() as mocker:
            update_properties = BindingConstraintPropertiesUpdate(enabled=False)
            creation_properties = BindingConstraintProperties(enabled=False)
            api_properties = BindingConstraintPropertiesAPI.from_user_model(creation_properties)
            constraint = BindingConstraint(
                "bc_1", ServiceFactory(self.api, self.study_id).create_binding_constraints_service()
            )
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint.id}"
            mocker.put(
                url,
                json={"id": "id", "name": "name", "terms": [], **api_properties.model_dump(mode="json")},
                status_code=200,
            )
            constraint.update_properties(properties=update_properties)
            assert constraint.properties == BindingConstraintProperties(enabled=False)

    def test_update_binding_constraint_properties_fails(self):
        with requests_mock.Mocker() as mocker:
            update_properties = BindingConstraintPropertiesUpdate(enabled=False)
            constraint = BindingConstraint(
                "bc_1", ServiceFactory(self.api, self.study_id).create_binding_constraints_service()
            )
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint.id}"
            antares_web_description_msg = "Server KO"
            mocker.put(url, json={"description": antares_web_description_msg}, status_code=404)

            with pytest.raises(
                ConstraintPropertiesUpdateError,
                match=f"Could not update properties for binding constraint {constraint.id}: {antares_web_description_msg}",
            ):
                constraint.update_properties(properties=update_properties)

    def test_update_binding_constraint_terms_success(self):
        with requests_mock.Mocker() as mocker:
            existing_term = ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=4, offset=3)
            service = ServiceFactory(self.api, self.study_id).create_binding_constraints_service()
            constraint = BindingConstraint("bc_1", service, None, [existing_term])

            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints/{constraint.id}/term"
            mocker.put(url, status_code=200)

            new_term = ConstraintTermUpdate(data=LinkData(area1="fr", area2="be"), weight=2)
            constraint.update_term(new_term)
            updated_term = constraint.get_terms()[existing_term.id]
            assert updated_term == ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=2, offset=3)

    def test_get_constraint_matrix_success(self, constraint_set):
        constraint = BindingConstraint(
            "bc_test", ServiceFactory(self.api, self.study_id).create_binding_constraints_service()
        )
        for matrix_method, enum_value, path, expected_matrix in constraint_set:
            with requests_mock.Mocker() as mocker:
                url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path={path}"
                mocker.get(url, json={"data": expected_matrix, "index": [0], "columns": [0]}, status_code=200)
                constraint_matrix = getattr(constraint, matrix_method)()
            assert constraint_matrix.equals(self.matrix)

    def test_get_constraint_matrix_fails(self, constraint_set):
        constraint = BindingConstraint(
            "bc_test", ServiceFactory(self.api, self.study_id).create_binding_constraints_service()
        )
        for matrix_method, enum_value, path, _ in constraint_set:
            with requests_mock.Mocker() as mocker:
                url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path={path}"
                mocker.get(url, json={"description": self.antares_web_description_msg}, status_code=404)
                with pytest.raises(
                    ConstraintMatrixDownloadError,
                    match=f"Could not download matrix {enum_value.value} for binding constraint {constraint.name}:",
                ):
                    getattr(constraint, matrix_method)()
