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

import numpy as np
import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    ConstraintMatrixDownloadError,
    ConstraintsPropertiesUpdateError,
    ConstraintTermEditionError,
)
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
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from tests.antares.services.api_services.utils import ARROW_CONTENT

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
    matrix = pd.DataFrame(np.zeros((8760, 1)))
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

    def test_update_binding_constraint_term_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            existing_term = ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=4, offset=3)
            constraint = BindingConstraint("bc_1", self.services.bc_service, None, [existing_term])

            url = f"{self.study_url}/bindingconstraints/{constraint.id}/term"
            mocker.put(url, status_code=200)

            new_term = ConstraintTermUpdate(data=LinkData(area1="fr", area2="be"), weight=2)
            constraint.update_term(new_term)
            updated_term = constraint.get_terms()[existing_term.id]
            assert updated_term == ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=2, offset=3)

    def test_update_binding_constraint_term_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            existing_term = ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=4, offset=3)
            constraint = BindingConstraint("bc_1", self.services.bc_service, None, [existing_term])

            url = f"{self.study_url}/bindingconstraints/{constraint.id}/term"
            mocker.put(url, json={"description": self.antares_web_description_msg}, status_code=422)

            new_term = ConstraintTermUpdate(data=LinkData(area1="fr", area2="be"), weight=2)
            with pytest.raises(
                ConstraintTermEditionError,
                match=f"Could not update the term '{new_term.id}' of the binding constraint '{constraint.id}': {self.antares_web_description_msg}",
            ):
                constraint.update_term(new_term)

    def test_get_constraint_matrix_success(self, constraint_set: fixture_type) -> None:
        constraint = BindingConstraint("bc_test", self.services.bc_service)
        for matrix_method, enum_value, path, expected_matrix in constraint_set:
            with requests_mock.Mocker() as mocker:
                url = f"{self.study_url}/raw?path={path}"
                mocker.get(url, content=ARROW_CONTENT, status_code=200)
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

    def test_delete_binding_constraint_term_encodes_term_id_with_percent(self) -> None:
        service = self.services.bc_service

        captured = {}

        class DummyWrapper:
            def delete(self, url: str) -> None:
                captured["url"] = url
                return None

        setattr(service, "_wrapper", DummyWrapper())

        constraint_id = "electrolysis-de"
        term_id = "_sink_00%de_el"

        service.delete_binding_constraint_term(constraint_id, term_id)

        assert captured["url"].endswith(f"bindingconstraints/{constraint_id}/term/_sink_00%25de_el")
