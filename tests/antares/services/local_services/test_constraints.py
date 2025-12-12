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

import re

from pathlib import Path

import pandas as pd

from antares.craft import BindingConstraintFrequency, Study
from antares.craft.exceptions.exceptions import (
    BindingConstraintCreationError,
    ConstraintDoesNotExistError,
    MatrixFormatError,
)
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintTerm,
    LinkData,
)
from antares.craft.service.local_services.factory import read_study_local
from antares.craft.tools.serde_local.ini_reader import IniReader


class TestBindingConstraints:
    def test_read_constraints(self, local_study_w_constraints: Study) -> None:
        study_path = Path(local_study_w_constraints.path)
        study = read_study_local(study_path)
        constraints = study.get_binding_constraints()
        assert len(constraints) == 2
        bc_1 = constraints["bc_1"]
        assert bc_1.name == "bc_1"
        assert bc_1.properties == BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
        assert bc_1.get_terms() == {}

        bc_2 = constraints["bc_2"]
        assert bc_2.name == "bc_2"
        assert bc_2.properties == BindingConstraintProperties()
        assert bc_2.get_terms() == {"at%fr": ConstraintTerm(data=LinkData(area1="at", area2="fr"), weight=2)}

    def test_update_properties(self, local_study_w_constraints: Study) -> None:
        # Checks values before update
        bc = local_study_w_constraints.get_binding_constraints()["bc_1"]
        current_properties = BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
        assert bc.properties == current_properties
        # Updates properties
        update_properties = BindingConstraintPropertiesUpdate(
            operator=BindingConstraintOperator.LESS, comments="new comment"
        )
        new_properties = bc.update_properties(update_properties)
        expected_properties = BindingConstraintProperties(
            enabled=False, operator=BindingConstraintOperator.LESS, comments="new comment"
        )
        assert new_properties == expected_properties
        assert bc.properties == expected_properties

    def test_update_multiple_update_properties(self, local_study_w_constraints: Study) -> None:
        # Checks values before update
        bc_1 = local_study_w_constraints.get_binding_constraints()["bc_1"]
        bc_2 = local_study_w_constraints.get_binding_constraints()["bc_2"]

        current_properties = BindingConstraintProperties(operator=BindingConstraintOperator.GREATER, enabled=False)
        assert bc_1.properties == current_properties
        assert bc_2.properties == BindingConstraintProperties()

        # Updates properties
        update_properties_1 = BindingConstraintPropertiesUpdate(group="group_1")
        update_properties_2 = BindingConstraintPropertiesUpdate(enabled=False)
        body = {bc_1.id: update_properties_1, bc_2.id: update_properties_2}
        local_study_w_constraints.update_binding_constraints(body)
        # Asserts constraints properties were modified
        assert bc_1.properties == BindingConstraintProperties(
            group="group_1", operator=BindingConstraintOperator.GREATER, enabled=False
        )
        assert bc_2.properties == BindingConstraintProperties(group="default", enabled=False)

    def test_matrices(self, local_study_w_constraints: Study) -> None:
        bc = local_study_w_constraints.get_binding_constraints()["bc_1"]

        # Replace matrices
        matrix = pd.DataFrame(data=8784 * [[3]])
        bc.set_greater_term(matrix)
        assert bc.get_greater_term_matrix().equals(matrix)

        bc.set_less_term(matrix)
        assert bc.get_less_term_matrix().equals(matrix)

        bc.set_equal_term(matrix)
        assert bc.get_equal_term_matrix().equals(matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for bindingconstraints/bc_1/bc_hourly matrix, expected shape is (8784, Any) and was : (2, 3)"
            ),
        ):
            bc.set_less_term(matrix)

    def test_delete(self, local_study_w_constraints: Study) -> None:
        bc = local_study_w_constraints.get_binding_constraints()["bc_1"]
        local_study_w_constraints.delete_binding_constraint(bc)
        assert bc.id not in local_study_w_constraints.get_binding_constraints()
        # Checks ini file
        study_path = Path(local_study_w_constraints.path)
        ini_content = IniReader().read(study_path / "input" / "bindingconstraints" / "bindingconstraints.ini")
        assert ini_content == {
            "0": {
                "at%fr": 2,
                "comments": "",
                "enabled": True,
                "filter-synthesis": "annual, daily, hourly, monthly, weekly",
                "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
                "group": "default",
                "id": "bc_2",
                "name": "bc_2",
                "operator": "less",
                "type": "hourly",
            }
        }

        # Asserts the matrix doesn't exist anymore
        matrix_path = study_path / "input" / "bindingconstraints" / f"{bc.id}_gt.txt"
        assert not matrix_path.exists()

        with pytest.raises(
            ConstraintDoesNotExistError,
            match=re.escape("The binding constraint 'bc_1' doesn't exist inside study 'studyTest'."),
        ):
            local_study_w_constraints.delete_binding_constraint(bc)

    def test_set_constraint_terms_success_add_and_replace_terms(self, local_study_w_constraints: Study) -> None:
        bc = local_study_w_constraints.get_binding_constraints()["bc_1"]
        constraint_term_1 = ConstraintTerm(data=LinkData(area1="ita", area2="fr"), weight=9, offset=7)
        constraint_term_2 = ConstraintTerm(data=LinkData(area1="fr", area2="be"), weight=1, offset=4)

        # adding terms on the binding constraint with the set_up
        bc.set_terms([constraint_term_1, constraint_term_2])
        assert list(bc.get_terms().values()) == [constraint_term_1, constraint_term_2]

        study_path = Path(local_study_w_constraints.path)

        ini_content = IniReader().read(study_path / "input" / "bindingconstraints" / "bindingconstraints.ini")
        actual_ini_content = ini_content["0"]

        expected_ini_content = {
            "be%fr": "1%4",
            "comments": "",
            "enabled": False,
            "filter-synthesis": "annual, daily, hourly, monthly, weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "fr%ita": "9%7",
            "group": "default",
            "id": "bc_1",
            "name": "bc_1",
            "operator": "greater",
            "type": "hourly",
        }

        assert actual_ini_content == expected_ini_content
        # end adding terms

        # replacing the old terms by new ones
        new_constraint_term_1 = ConstraintTerm(data=LinkData(area1="de", area2="en"), weight=0, offset=3)
        new_constraint_term_2 = ConstraintTerm(data=LinkData(area1="tu", area2="po"), weight=5, offset=10)

        bc.set_terms([new_constraint_term_1, new_constraint_term_2])
        assert list(bc.get_terms().values()) == [new_constraint_term_1, new_constraint_term_2]

        expected_new_first_ini_content = {
            "comments": "",
            "de%en": "0%3",
            "enabled": False,
            "filter-synthesis": "annual, daily, hourly, monthly, weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "group": "default",
            "id": "bc_1",
            "name": "bc_1",
            "operator": "greater",
            "po%tu": "5%10",
            "type": "hourly",
        }

        ini_content = IniReader().read(study_path / "input" / "bindingconstraints" / "bindingconstraints.ini")
        actual_first_ini_content = ini_content["0"]

        assert actual_first_ini_content == expected_new_first_ini_content
        # end replacing

    def test_set_constraint_terms_fail_existing_constraint(self, local_study_w_constraints: Study) -> None:
        bc = BindingConstraint("bc", local_study_w_constraints._binding_constraints_service)
        study_name = local_study_w_constraints.name

        with pytest.raises(
            ConstraintDoesNotExistError,
            match=f"The binding constraint '{bc.name}' doesn't exist inside study '{study_name}'.",
        ):
            bc.set_terms([])

    def test_create_bc_with_wrong_matrices(self, local_study: Study) -> None:
        name = "bc1"
        default_matrix = pd.DataFrame(data=8784 * [[3]])

        # Less operator
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.LESS)
        msg = "You cannot fill matrices '['equal_term_matrix', 'greater_term_matrix']' while using the operator 'less'"
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, equal_term_matrix=default_matrix)
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, greater_term_matrix=default_matrix)

        # Equal operator
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.EQUAL)
        msg = "You cannot fill matrices '['less_term_matrix', 'greater_term_matrix']' while using the operator 'equal'"
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, greater_term_matrix=default_matrix)
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, less_term_matrix=default_matrix)

        # Both operator
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.BOTH)
        msg = "You cannot fill matrices '['equal_term_matrix']' while using the operator 'both'"
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, equal_term_matrix=default_matrix)

        # Greater operator
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.GREATER)
        msg = "You cannot fill matrices '['less_term_matrix', 'equal_term_matrix']' while using the operator 'greater'"
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, equal_term_matrix=default_matrix)
        with pytest.raises(BindingConstraintCreationError, match=re.escape(msg)):
            local_study.create_binding_constraint(name=name, properties=properties, less_term_matrix=default_matrix)

    def test_create_bc_creates_only_needed_matrices(self, local_study: Study) -> None:
        name = "bc1"
        default_matrix = pd.DataFrame(data=8784 * [[3]])
        properties = BindingConstraintProperties(operator=BindingConstraintOperator.LESS)
        bc = local_study.create_binding_constraint(name=name, properties=properties, less_term_matrix=default_matrix)
        assert bc.get_less_term_matrix().equals(default_matrix)
        # Checks only one matrix is created
        bc_folder = Path(local_study.path) / "input" / "bindingconstraints"
        matrices = list(bc_folder.glob("*.txt"))
        assert len(matrices) == 1
        assert matrices[0].name == "bc1_lt.txt"

    def test_modify_constraint_time_step(self, local_study_with_constraint: Study) -> None:
        bc = local_study_with_constraint.get_binding_constraints()["test constraint"]
        # Set a matrix with specific values
        matrix = pd.DataFrame(data=8784 * [[3]])
        bc.set_less_term(matrix)
        # Asserts the matrix is saved correctly
        assert bc.get_less_term_matrix().equals(matrix)
        # Update the timestep
        new_properties = BindingConstraintPropertiesUpdate(time_step=BindingConstraintFrequency.DAILY)
        bc.update_properties(new_properties)
        # Assert the matrix was reset to its default value
        assert bc.get_less_term_matrix().equals(pd.DataFrame(366 * [[0.0]]))
