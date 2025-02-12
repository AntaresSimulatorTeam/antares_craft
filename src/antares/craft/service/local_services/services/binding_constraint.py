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
from typing import Any, Optional, Union

import numpy as np
import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    BindingConstraintCreationError,
    ConstraintDoesNotExistError,
)
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintMatrixName,
    ConstraintTerm,
)
from antares.craft.service.base_services import BaseBindingConstraintService
from antares.craft.service.local_services.models.binding_constraint import BindingConstraintPropertiesLocal
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import df_read, df_save
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class BindingConstraintLocalService(BaseBindingConstraintService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.ini_file = IniFile(self.config.study_path, InitializationFilesTypes.BINDING_CONSTRAINTS_INI)

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

        self._create_constraint_inside_ini(name, local_properties, terms)

        self._store_time_series(constraint, less_term_matrix, equal_term_matrix, greater_term_matrix)

        return constraint

    @staticmethod
    def _create_local_property_args(constraint: BindingConstraint) -> dict[str, Union[str, dict[str, ConstraintTerm]]]:
        return {
            "constraint_name": constraint.name,
            "constraint_id": constraint.id,
            "terms": constraint.get_terms(),
            **constraint.properties.model_dump(mode="json", exclude_none=True),
        }

    def _generate_local_properties(self, constraint: BindingConstraint) -> BindingConstraintPropertiesLocal:
        return BindingConstraintPropertiesLocal.model_validate(self._create_local_property_args(constraint))

    def _store_time_series(
        self,
        constraint: BindingConstraint,
        less_term_matrix: Optional[pd.DataFrame],
        equal_term_matrix: Optional[pd.DataFrame],
        greater_term_matrix: Optional[pd.DataFrame],
    ) -> None:
        time_series = []
        file_types = []
        # Lesser or greater can happen together when operator is both
        if constraint.properties.operator in (BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH):
            time_series += [self._check_if_empty_ts(constraint.properties.time_step, less_term_matrix)]
            file_types += [TimeSeriesFileType.BINDING_CONSTRAINT_LESS]
        if constraint.properties.operator in (BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH):
            time_series += [self._check_if_empty_ts(constraint.properties.time_step, greater_term_matrix)]
            file_types += [TimeSeriesFileType.BINDING_CONSTRAINT_GREATER]
        # Equal is always exclusive
        if constraint.properties.operator == BindingConstraintOperator.EQUAL:
            time_series = [self._check_if_empty_ts(constraint.properties.time_step, equal_term_matrix)]
            file_types = [TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL]

        for ts, file_type in zip(time_series, file_types):
            matrix_path = self.config.study_path.joinpath(file_type.value.format(constraint_id=constraint.id))
            df_save(ts, matrix_path)

    @staticmethod
    def _check_if_empty_ts(time_step: BindingConstraintFrequency, time_series: Optional[pd.DataFrame]) -> pd.DataFrame:
        time_series_length = (365 * 24 + 24) if time_step == BindingConstraintFrequency.HOURLY else 366
        return time_series if time_series is not None else pd.DataFrame(np.zeros([time_series_length, 1]))

    def _create_constraint_inside_ini(
        self,
        constraint_name: str,
        properties: BindingConstraintPropertiesLocal,
        terms: Optional[list[ConstraintTerm]] = None,
    ) -> None:
        current_ini_content = self.ini_file.ini_dict
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
        term_content = {} if not terms else {term.id: term.weight_offset() for term in terms}
        whole_content = props_content | term_content
        current_ini_content[new_key] = whole_content
        self.ini_file.ini_dict = current_ini_content
        self.ini_file.write_ini_file()

    def _write_binding_constraint_ini(
        self,
        local_properties: BindingConstraintPropertiesLocal,
        constraint_name: str,
        terms: Optional[list[ConstraintTerm]] = None,
    ) -> None:
        """
        Write or update a binding constraint in the INI file.

        """

        current_ini_content = self.ini_file.ini_dict_binding_constraints or {}

        existing_section = next(
            (section for section, values in current_ini_content.items() if values.get("name") == constraint_name),
            None,
        )

        if existing_section:
            existing_terms = current_ini_content[existing_section]

            serialized_terms = {term.id: term.weight_offset() for term in terms} if terms else {}

            existing_terms.update(serialized_terms)
            current_ini_content[existing_section] = existing_terms

            # Persist the updated INI content
            self.ini_file.write_ini_file()
        else:
            section_index = len(current_ini_content)
            current_ini_content[str(section_index)] = local_properties.list_ini_fields

        self.ini_file.ini_dict_binding_constraints = current_ini_content
        self.ini_file.write_ini_file()

    @override
    def add_constraint_terms(self, constraint: BindingConstraint, terms: list[ConstraintTerm]) -> list[ConstraintTerm]:
        """
        Add terms to a binding constraint and update the INI file.

        Args:
            constraint (BindingConstraint): The binding constraint to update.
            terms (list[ConstraintTerm]): A list of new terms to add.

        Returns:
            list[ConstraintTerm]: The updated list of terms.
        """

        new_terms = constraint.get_terms().copy()

        for term in terms:
            if term.id in constraint.get_terms():
                raise BindingConstraintCreationError(
                    constraint_name=constraint.name, message=f"Duplicate term found: {term.id}"
                )
            new_terms[term.id] = term

        local_properties = self._generate_local_properties(constraint)
        local_properties.terms = new_terms

        terms_values = list(new_terms.values())

        self._write_binding_constraint_ini(
            local_properties=local_properties,
            constraint_name=constraint.name,
            terms=terms_values,
        )

        return terms_values

    @override
    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    @override
    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintPropertiesUpdate
    ) -> BindingConstraintProperties:
        current_ini_content = self.ini_file.ini_dict
        # Ensures the constraint already exists
        existing_key = next((key for key, bc in current_ini_content.items() if bc["id"] == binding_constraint.id), None)
        if not existing_key:
            raise ConstraintDoesNotExistError(binding_constraint.name)

        local_properties = BindingConstraintPropertiesLocal.from_user_model(properties)
        existing_constraint = current_ini_content[existing_key]
        existing_constraint.update(local_properties.model_dump(mode="json", by_alias=True))
        self.ini_file.ini_dict = current_ini_content
        self.ini_file.write_ini_file()
        return local_properties.to_user_model()

    @override
    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        file_path = self.config.study_path.joinpath(
            "input", "bindingconstraints", f"{constraint.id}_{matrix_name.value}.txt"
        )
        return df_read(file_path)

    @override
    def update_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        raise NotImplementedError

    @override
    def read_binding_constraints(self) -> list[BindingConstraint]:
        raise NotImplementedError
