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
import copy

from typing import Any, Optional

import numpy as np
import pandas as pd

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    BindingConstraintCreationError,
    ConstraintDoesNotExistError,
    ConstraintPropertiesUpdateError,
)
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintMatrixName,
    ConstraintTerm,
    ConstraintTermData,
    ConstraintTermUpdate,
)
from antares.craft.service.base_services import BaseBindingConstraintService
from antares.craft.service.local_services.models.binding_constraint import BindingConstraintPropertiesLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType

MAPPING = {
    ConstraintMatrixName.LESS_TERM: TimeSeriesFileType.BINDING_CONSTRAINT_LESS,
    ConstraintMatrixName.EQUAL_TERM: TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL,
    ConstraintMatrixName.GREATER_TERM: TimeSeriesFileType.BINDING_CONSTRAINT_GREATER,
}

DEFAULT_VALUE_MAPPING = {
    BindingConstraintFrequency.HOURLY: (8784, 1),
    BindingConstraintFrequency.WEEKLY: (366, 1),
    BindingConstraintFrequency.DAILY: (366, 1),
}


class BindingConstraintLocalService(BaseBindingConstraintService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self._ini_path = self.config.study_path / "input" / "bindingconstraints" / "bindingconstraints.ini"

    @override
    def create_binding_constraint(
        self,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[list[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
        properties = properties or BindingConstraintProperties()
        constraint = BindingConstraint(
            name=name,
            binding_constraint_service=self,
            properties=properties,
            terms=terms,
        )

        local_properties = BindingConstraintPropertiesLocal.from_user_model(properties)

        self._create_constraint_inside_ini(name, local_properties, terms or [])

        # Save matrices
        mapping = {
            ConstraintMatrixName.LESS_TERM: less_term_matrix,
            ConstraintMatrixName.EQUAL_TERM: equal_term_matrix,
            ConstraintMatrixName.GREATER_TERM: greater_term_matrix,
        }
        for matrix_name, matrix in mapping.items():
            matrix = matrix if matrix is not None else pd.DataFrame()
            self.set_constraint_matrix(constraint, matrix_name, matrix)

        return constraint

    def _read_ini(self) -> dict[str, Any]:
        return IniReader().read(self._ini_path)

    def _save_ini(self, content: dict[str, Any]) -> None:
        IniWriter().write(content, self._ini_path)

    def _create_constraint_inside_ini(
        self,
        constraint_name: str,
        properties: BindingConstraintPropertiesLocal,
        terms: list[ConstraintTerm],
    ) -> None:
        current_ini_content = self._read_ini()
        constraint_id = transform_name_to_id(constraint_name)
        # Ensures the constraint doesn't already exist
        for existing_constraint in current_ini_content.values():
            if existing_constraint["id"] == constraint_id:
                raise BindingConstraintCreationError(
                    constraint_name=constraint_name,
                    message=f"A binding constraint with the name {constraint_name} already exists.",
                )
        new_key = str(len(current_ini_content.keys()))
        props_content = {
            "id": constraint_id,
            "name": constraint_name,
            **properties.model_dump(mode="json", by_alias=True),
        }
        term_content = {term.id: term.weight_offset() for term in terms}
        whole_content = props_content | term_content
        current_ini_content[new_key] = whole_content
        self._save_ini(current_ini_content)

    @override
    def add_constraint_terms(self, constraint: BindingConstraint, terms: list[ConstraintTerm]) -> None:
        """
        Add terms to a binding constraint and update the INI file.

        Args:
            constraint (BindingConstraint): The binding constraint to update.
            terms (list[ConstraintTerm]): A list of new terms to add.
        """

        # Checks the terms to add are not already defined
        current_terms = constraint.get_terms()
        new_terms = {}
        for term in terms:
            if term.id in current_terms:
                raise BindingConstraintCreationError(
                    constraint_name=constraint.name, message=f"Duplicate term found: {term.id}"
                )
            new_terms[term.id] = term.weight_offset()

        current_ini_content = self._read_ini()

        # Look for the constraint
        existing_key = next((key for key, bc in current_ini_content.items() if bc["id"] == constraint.id), None)
        if not existing_key:
            raise ConstraintDoesNotExistError(constraint.name, self.study_name)

        current_ini_content[existing_key].update(new_terms)
        self._save_ini(current_ini_content)

    @override
    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    @override
    def update_binding_constraint_term(
        self, constraint_id: str, term: ConstraintTermUpdate, existing_term: ConstraintTerm
    ) -> ConstraintTerm:
        raise NotImplementedError

    @override
    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        df = read_timeseries(MAPPING[matrix_name], self.config.study_path, constraint_id=constraint.id)
        if not df.empty:
            return df
        default_matrix_shape = DEFAULT_VALUE_MAPPING[constraint.properties.time_step]
        return pd.DataFrame(np.zeros(default_matrix_shape))

    @override
    def set_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        checks_matrix_dimensions(
            matrix, f"bindingconstraints/{constraint.id}", f"bc_{constraint.properties.time_step.value}"
        )
        write_timeseries(
            self.config.study_path,
            matrix,
            MAPPING[matrix_name],
            constraint_id=constraint.id,
        )

    @override
    def read_binding_constraints(self) -> dict[str, BindingConstraint]:
        constraints: dict[str, BindingConstraint] = {}
        current_ini_content = self._read_ini()
        for constraint in current_ini_content.values():
            name = constraint.pop("name")
            del constraint["id"]

            # Separate properties from terms
            properties_fields = BindingConstraintPropertiesLocal().model_dump(by_alias=True)  # type: ignore
            terms_dict = {}
            local_properties_dict = {}
            for k, v in constraint.items():
                if k in properties_fields:
                    local_properties_dict[k] = v
                else:
                    terms_dict[k] = v

            # Build properties
            local_properties = BindingConstraintPropertiesLocal.model_validate(local_properties_dict)
            properties = local_properties.to_user_model()

            # Build terms
            terms = []
            for key, value in terms_dict.items():
                term_data = ConstraintTermData.from_ini(key)
                if "%" in str(value):
                    weight, offset = value.split("%")
                else:
                    weight = value
                    offset = 0
                term = ConstraintTerm(weight=float(weight), offset=int(offset), data=term_data)
                terms.append(term)

            bc = BindingConstraint(name=name, binding_constraint_service=self, properties=properties, terms=terms)
            constraints[bc.id] = bc

        return constraints

    @override
    def update_binding_constraints_properties(
        self, new_properties: dict[str, BindingConstraintPropertiesUpdate]
    ) -> dict[str, BindingConstraintProperties]:
        new_properties_dict: dict[str, BindingConstraintProperties] = {}
        all_constraint_to_update = set(new_properties.keys())  # used to raise an Exception if a bc doesn't exist

        current_ini_content = self._read_ini()
        for key, constraint in current_ini_content.items():
            constraint_id = constraint["id"]
            if constraint_id in new_properties:
                all_constraint_to_update.remove(constraint_id)

                # Performs the update
                local_properties = BindingConstraintPropertiesLocal.from_user_model(new_properties[constraint_id])
                constraint.update(local_properties.model_dump(mode="json", by_alias=True, exclude_unset=True))

                # Prepare the object to return
                local_dict = copy.deepcopy(constraint)
                del local_dict["name"]
                del local_dict["id"]
                local_properties = BindingConstraintPropertiesLocal.model_validate(local_dict)
                new_properties_dict[constraint_id] = local_properties.to_user_model()

        if len(all_constraint_to_update) > 0:
            raise ConstraintPropertiesUpdateError(next(iter(all_constraint_to_update)), "The bc does not exist")

        # Update ini file
        self._save_ini(current_ini_content)

        return new_properties_dict

    def _get_constraint_inside_ini(self, ini_content: dict[str, Any], constraint: BindingConstraint) -> dict[str, Any]:
        existing_key = next((key for key, bc in ini_content.items() if bc["id"] == constraint.id), None)
        if not existing_key:
            raise ConstraintDoesNotExistError(constraint.name, self.study_name)

        return ini_content[existing_key]  # type: ignore
