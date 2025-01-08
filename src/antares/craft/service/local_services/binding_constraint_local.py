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
from antares.craft.exceptions.exceptions import BindingConstraintCreationError
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    ConstraintMatrixName,
    ConstraintTerm,
    DefaultBindingConstraintProperties,
)
from antares.craft.service.base_services import BaseBindingConstraintService
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import df_read, df_save
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from pydantic import Field


class BindingConstraintPropertiesLocal(DefaultBindingConstraintProperties):
    """
    Used to create the entries for the bindingconstraints.ini file

    Attributes:
        constraint_name: The constraint name
        constraint_id: The constraint id
        properties (BindingConstraintProperties): The BindingConstraintProperties  to set
        terms (dict[str, ConstraintTerm]]): The terms applying to the binding constraint
    """

    constraint_name: str
    constraint_id: str
    terms: dict[str, ConstraintTerm] = Field(default_factory=dict[str, ConstraintTerm])

    @property
    def list_ini_fields(self) -> dict[str, str]:
        ini_dict = {
            "name": self.constraint_name,
            "id": self.constraint_id,
            "enabled": f"{self.enabled}".lower(),
            "type": self.time_step.value,
            "operator": self.operator.value,
            "comments": self.comments,
            "filter-year-by-year": self.filter_year_by_year,
            "filter-synthesis": self.filter_synthesis,
            "group": self.group,
        } | {term_id: term.weight_offset() for term_id, term in self.terms.items()}
        return {key: value for key, value in ini_dict.items() if value not in [None, ""]}

    def yield_binding_constraint_properties(self) -> BindingConstraintProperties:
        excludes = {
            "constraint_name",
            "constraint_id",
            "terms",
            "list_ini_fields",
        }
        return BindingConstraintProperties(**self.model_dump(mode="json", exclude=excludes))


class BindingConstraintLocalService(BaseBindingConstraintService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
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

        local_properties = self._generate_local_properties(constraint)
        constraint.properties = local_properties.yield_binding_constraint_properties()

        current_ini_content = self.ini_file.ini_dict_binding_constraints or {}
        if any(values.get("id") == constraint.id for values in current_ini_content.values()):
            raise BindingConstraintCreationError(
                constraint_name=name, message=f"A binding constraint with the name {name} already exists."
            )

        self._write_binding_constraint_ini(local_properties, name, name, terms)

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

    def _write_binding_constraint_ini(
        self,
        local_properties: BindingConstraintPropertiesLocal,
        constraint_name: str,
        constraint_id: str,
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

            existing_terms.update(serialized_terms)  # type: ignore
            current_ini_content[existing_section] = existing_terms

            # Persist the updated INI content
            self.ini_file.write_ini_file()
        else:
            section_index = len(current_ini_content)
            current_ini_content[str(section_index)] = local_properties.list_ini_fields

        self.ini_file.ini_dict_binding_constraints = current_ini_content
        self.ini_file.write_ini_file()

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
            constraint_id=constraint.id,
            terms=terms_values,
        )

        return terms_values

    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintProperties
    ) -> BindingConstraintProperties:
        raise NotImplementedError

    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        file_path = self.config.study_path.joinpath(
            "input", "bindingconstraints", f"{constraint.id}_{matrix_name.value}.txt"
        )
        return df_read(file_path)

    def update_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        raise NotImplementedError

    def read_binding_constraints(self) -> list[BindingConstraint]:
        raise NotImplementedError
