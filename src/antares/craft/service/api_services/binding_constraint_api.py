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

from pathlib import PurePosixPath
from typing import List, Optional

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    BindingConstraintCreationError,
    ConstraintMatrixDownloadError,
    ConstraintMatrixUpdateError,
    ConstraintPropertiesUpdateError,
    ConstraintRetrievalError,
    ConstraintTermAdditionError,
    ConstraintTermDeletionError,
)
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    ConstraintMatrixName,
    ConstraintTerm,
)
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseBindingConstraintService


class BindingConstraintApiService(BaseBindingConstraintService):
    def __init__(self, config: APIconf, study_id: str) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

    def create_binding_constraint(
        self,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[List[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
        """
        Args:
            name: the binding constraint name
            properties: the properties of the constraint. If not provided, AntaresWeb will use its own default values.
            terms: the terms of the constraint. If not provided, no term will be created.
            less_term_matrix: matrix corresponding to the lower bound of the constraint. If not provided, no matrix will be created.
            equal_term_matrix: matrix corresponding to the equality bound of the constraint. If not provided, no matrix will be created.
            greater_term_matrix: matrix corresponding to the upper bound of the constraint. If not provided, no matrix will be created.

        Returns:
            The created binding constraint

        Raises:
            MissingTokenError if api_token is missing
            BindingConstraintCreationError if an HTTP Exception occurs
        """
        base_url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints"

        try:
            body = {"name": name}
            if properties:
                camel_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            for matrix, matrix_name in zip(
                [less_term_matrix, equal_term_matrix, greater_term_matrix],
                ["lessTermMatrix", "equalTermMatrix", "greaterTermMatrix"],
            ):
                if matrix is not None:
                    body[matrix_name] = matrix.to_numpy().tolist()
            response = self._wrapper.post(base_url, json=body)
            created_properties = response.json()
            bc_id = created_properties["id"]
            for key in ["terms", "id", "name"]:
                del created_properties[key]
            bc_properties = BindingConstraintProperties.model_validate(created_properties)
            bc_terms: List[ConstraintTerm] = []

            if terms:
                json_terms = [term.model_dump() for term in terms]
                url = f"{base_url}/{bc_id}/terms"
                self._wrapper.post(url, json=json_terms)

                url = f"{base_url}/{bc_id}"
                response = self._wrapper.get(url)
                created_terms = response.json()["terms"]
                bc_terms = [ConstraintTerm.model_validate(term) for term in created_terms]

        except APIError as e:
            raise BindingConstraintCreationError(name, e.message) from e

        constraint = BindingConstraint(name, self, bc_properties, bc_terms)

        return constraint

    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint_id}/term/{term_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise ConstraintTermDeletionError(constraint_id, term_id, e.message) from e

    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintProperties
    ) -> BindingConstraintProperties:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{binding_constraint.id}"
        try:
            body = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not body:
                return binding_constraint.properties

            response = self._wrapper.put(url, json=body)
            json_response = response.json()
            for key in ["terms", "id", "name"]:
                del json_response[key]
            new_properties = BindingConstraintProperties.model_validate(json_response)

        except APIError as e:
            raise ConstraintPropertiesUpdateError(binding_constraint.id, e.message) from e

        return new_properties

    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        try:
            path = PurePosixPath("input") / "bindingconstraints" / f"{constraint.id}_{matrix_name.value}"
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise ConstraintMatrixDownloadError(constraint.id, matrix_name.value, e.message) from e

    def update_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        mapping = {
            ConstraintMatrixName.LESS_TERM: "lessTermMatrix",
            ConstraintMatrixName.GREATER_TERM: "greaterTermMatrix",
            ConstraintMatrixName.EQUAL_TERM: "equalTermMatrix",
        }
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint.id}"
        try:
            body = {mapping[matrix_name]: matrix.to_numpy().tolist()}
            self._wrapper.put(url, json=body)
        except APIError as e:
            raise ConstraintMatrixUpdateError(constraint.id, matrix_name.value, e.message) from e

    def add_constraint_terms(self, constraint: BindingConstraint, terms: List[ConstraintTerm]) -> List[ConstraintTerm]:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint.id}"
        try:
            json_terms = [term.model_dump() for term in terms]
            self._wrapper.post(f"{url}/terms", json=json_terms)
            response = self._wrapper.get(url)
            all_terms = response.json()["terms"]
            validated_terms = [ConstraintTerm.model_validate(term) for term in all_terms]
            new_terms = [term for term in validated_terms if term.id not in constraint.get_terms()]

        except APIError as e:
            raise ConstraintTermAdditionError(constraint.id, [term.id for term in terms], e.message) from e

        return new_terms

    def read_binding_constraints(self) -> list[BindingConstraint]:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints"
        try:
            response = self._wrapper.get(url)
            constraints_json = response.json()

            constraints = [
                BindingConstraint(
                    constraint["name"],
                    self,
                    BindingConstraintProperties.model_validate(
                        {k: v for k, v in constraint.items() if k not in ["terms", "id", "name"]}
                    ),
                    [ConstraintTerm.model_validate(term) for term in constraint["terms"]],
                )
                for constraint in constraints_json
            ]
            constraints.sort(key=lambda constraint: constraint.id)
            return constraints
        except APIError as e:
            raise ConstraintRetrievalError(self.study_id, e.message) from e
