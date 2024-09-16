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

from typing import Optional, List, Any

import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.model.binding_constraint import (
    BindingConstraintProperties,
    ConstraintTerm,
    BindingConstraint,
    ConstraintMatrixName,
)
from antares.service.base_services import BaseBindingConstraintService
from antares.tools.ini_tool import IniFile, IniFileTypes


class BindingConstraintLocalService(BaseBindingConstraintService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.binding_constraints: dict[str, BindingConstraint] = {}
        self.ini_file = IniFile(self.config.study_path, IniFileTypes.BINDING_CONSTRAINTS_INI)

    def create_binding_constraint(
        self,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[list[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
        constraint = BindingConstraint(
            name=name,
            binding_constraint_service=self,
            properties=properties,
            terms=terms,
        )
        constraint.properties = constraint.local_properties.yield_binding_constraint_properties
        self.binding_constraints[constraint.id] = constraint

        self._write_binding_constraint_ini()

        return constraint

    def _write_binding_constraint_ini(self) -> None:
        binding_constraints_ini_content = {
            idx: idx_constraint.local_properties.list_ini_fields
            for idx, idx_constraint in enumerate(self.binding_constraints.values())
        }
        self.ini_file.ini_dict = binding_constraints_ini_content
        self.ini_file.write_ini_file()

    def add_constraint_terms(self, constraint: BindingConstraint, terms: list[ConstraintTerm]) -> list[ConstraintTerm]:
        for term in terms:
            term.weight = term.weight if term.weight is not None else 0
        new_terms = constraint.local_properties.terms | {
            term.id: term for term in terms if term.id not in constraint.get_terms()
        }
        constraint.local_properties.terms = new_terms
        self._write_binding_constraint_ini()
        return list(new_terms.values())

    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintProperties
    ) -> BindingConstraintProperties:
        raise NotImplementedError

    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        raise NotImplementedError

    def update_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        raise NotImplementedError
