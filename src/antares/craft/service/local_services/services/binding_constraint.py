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
from typing import Any, Optional

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
    ConstraintTermUpdate,
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

        self._create_constraint_inside_ini(name, local_properties, terms or [])

        self._store_time_series(constraint, less_term_matrix, equal_term_matrix, greater_term_matrix)

        return constraint

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
        terms: list[ConstraintTerm],
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
        term_content = {term.id: term.weight_offset() for term in terms}
        whole_content = props_content | term_content
        current_ini_content[new_key] = whole_content
        self.ini_file.ini_dict = current_ini_content
        self.ini_file.write_ini_file()

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
        for term in terms:
            if term.id in current_terms:
                raise BindingConstraintCreationError(
                    constraint_name=constraint.name, message=f"Duplicate term found: {term.id}"
                )

        current_ini_content = self.ini_file.ini_dict_binding_constraints or {}
        existing_constraint = self._get_constraint_inside_ini(current_ini_content, constraint)
        new_terms = {term.id: term.weight_offset() for term in terms}
        existing_constraint.update(new_terms)
        self.ini_file.ini_dict = current_ini_content
        self.ini_file.write_ini_file()

    @override
    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    @override
    def update_binding_constraint_term(
        self, constraint_id: str, term: ConstraintTermUpdate, existing_term: ConstraintTerm
    ) -> ConstraintTerm:
        raise NotImplementedError

    @override
    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintPropertiesUpdate
    ) -> BindingConstraintProperties:
        current_ini_content = self.ini_file.ini_dict
        existing_constraint = self._get_constraint_inside_ini(current_ini_content, binding_constraint)
        local_properties = BindingConstraintPropertiesLocal.from_user_model(properties)
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

    @staticmethod
    def _get_constraint_inside_ini(ini_content: dict[str, Any], constraint: BindingConstraint) -> dict[str, Any]:
        existing_key = next((key for key, bc in ini_content.items() if bc["id"] == constraint.id), None)
        if not existing_key:
            raise ConstraintDoesNotExistError(constraint.name)

        return ini_content[existing_key]  # type: ignore
