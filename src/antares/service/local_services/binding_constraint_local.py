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

from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import BindingConstraintCreationError
from antares.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesLocal,
    ConstraintMatrixName,
    ConstraintTerm,
)
from antares.service.base_services import BaseBindingConstraintService
from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.matrix_tool import df_save
from antares.tools.time_series_tool import TimeSeriesFileType


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
        constraint.properties = constraint.local_properties.yield_binding_constraint_properties()

        self._write_binding_constraint_ini(constraint.properties, name, name, terms)

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
        time_series_ids = []
        file_types = []
        # Lesser or greater can happen together when operator is both
        if constraint.properties.operator in (BindingConstraintOperator.LESS, BindingConstraintOperator.BOTH):
            time_series += [self._check_if_empty_ts(constraint.properties.time_step, less_term_matrix)]
            time_series_ids += [f"{constraint.id.lower()}_lt"]
            file_types += [TimeSeriesFileType.BINDING_CONSTRAINT_LESS]
        if constraint.properties.operator in (BindingConstraintOperator.GREATER, BindingConstraintOperator.BOTH):
            time_series += [self._check_if_empty_ts(constraint.properties.time_step, greater_term_matrix)]
            time_series_ids += [f"{constraint.id.lower()}_gt"]
            file_types += [TimeSeriesFileType.BINDING_CONSTRAINT_GREATER]
        # Equal is always exclusive
        if constraint.properties.operator == BindingConstraintOperator.EQUAL:
            time_series = [self._check_if_empty_ts(constraint.properties.time_step, equal_term_matrix)]
            time_series_ids = [f"{constraint.id.lower()}_eq"]
            file_types = [TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL]

        for ts, ts_id, file_type in zip(time_series, time_series_ids, file_types):
            matrix_path = self.config.study_path.joinpath(file_type.value.format(constraint_id=constraint.id))
            df_save(ts, matrix_path)

    @staticmethod
    def _check_if_empty_ts(time_step: BindingConstraintFrequency, time_series: Optional[pd.DataFrame]) -> pd.DataFrame:
        time_series_length = (365 * 24 + 24) if time_step == BindingConstraintFrequency.HOURLY else 366
        return time_series if time_series is not None else pd.DataFrame(np.zeros([time_series_length, 1]))

    def _write_binding_constraint_ini(
        self,
        properties: BindingConstraintProperties,
        constraint_name: str,
        constraint_id: str,
        terms: Optional[list[ConstraintTerm]] = None,
    ) -> None:
        """
        Write a single binding constraint to the INI file, reconstructing a full BindingConstraintPropertiesLocal instance.

        Args:
            properties (BindingConstraintProperties): Basic properties of the binding constraint.
            constraint_name (str): The name of the constraint.
            constraint_id (str): The ID of the constraint.
            terms (dict[str, ConstraintTerm], optional): Terms applying to the binding constraint. Defaults to None.
        Raises:
        BindingConstraintCreationError: If a binding constraint with the same name already exists in the INI file.
        """

        current_ini_content = self.ini_file.ini_dict or {}

        if constraint_name in current_ini_content:
            if terms in [None, {}]:
                raise BindingConstraintCreationError(
                    constraint_name=constraint_name,
                    message=f"A binding constraint with the name {constraint_name} already exists with terms.",
                )

        terms_dict = {term.id: term for term in terms} if terms else {}

        full_properties = BindingConstraintPropertiesLocal(
            constraint_name=constraint_name, constraint_id=constraint_id, terms=terms_dict, **properties.model_dump()
        )

        current_ini_content = self.ini_file.ini_dict or {}

        current_ini_content[full_properties.constraint_name] = full_properties.list_ini_fields

        self.ini_file.ini_dict = current_ini_content

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

        new_terms = {
            **constraint.local_properties.terms,  # Existing terms
            **{term.id: term for term in terms if term.id not in constraint.get_terms()},  # New terms
        }

        constraint.local_properties.terms = new_terms

        list(new_terms.values())

        self._write_binding_constraint_ini(
            properties=constraint.properties,
            constraint_name=constraint.name,
            constraint_id=constraint.id,
            terms=list(new_terms.values()),
        )

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
