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
from dataclasses import asdict, replace
from pathlib import PurePosixPath
from typing import Any, Optional

import pandas as pd

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    BindingConstraintCreationError,
    ConstraintMatrixDownloadError,
    ConstraintMatrixUpdateError,
    ConstraintRetrievalError,
    ConstraintsPropertiesUpdateError,
    ConstraintTermAdditionError,
    ConstraintTermDeletionError,
    ConstraintTermEditionError,
)
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    ConstraintMatrixName,
    ConstraintTerm,
    ConstraintTermData,
    ConstraintTermUpdate,
)
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseBindingConstraintService


class BindingConstraintApiService(BaseBindingConstraintService):
    def __init__(self, config: APIconf, study_id: str) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

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
                api_model = BindingConstraintPropertiesAPI.from_user_model(properties)
                camel_properties = api_model.model_dump(mode="json", by_alias=True, exclude_none=True)
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
            api_properties = BindingConstraintPropertiesAPI.model_validate(created_properties)
            bc_properties = api_properties.to_user_model()

            if terms:
                json_terms = [
                    {"weight": term.weight, "offset": term.offset, "data": asdict(term.data)} for term in terms
                ]
                url = f"{base_url}/{bc_id}/terms"
                self._wrapper.post(url, json=json_terms)

        except APIError as e:
            raise BindingConstraintCreationError(name, e.message) from e

        constraint = BindingConstraint(name, self, bc_properties, terms)

        return constraint

    @override
    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint_id}/term/{term_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise ConstraintTermDeletionError(constraint_id, term_id, e.message) from e

    @override
    def update_binding_constraint_term(
        self, constraint_id: str, term: ConstraintTermUpdate, existing_term: ConstraintTerm
    ) -> ConstraintTerm:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint_id}/term"
        try:
            body: dict[str, Any] = {
                "id": existing_term.id,
                "data": asdict(term.data),
                "weight": term.weight or existing_term.weight,
            }
            if term.offset:
                body["offset"] = term.offset
            self._wrapper.put(url, json=body)
        except APIError as e:
            raise ConstraintTermEditionError(constraint_id, term.id, e.message) from e

        # Copies object to bypass the fact that the class is frozen
        if term.weight:
            existing_term = replace(existing_term, weight=term.weight)
        if term.offset:
            existing_term = replace(existing_term, offset=term.offset)
        return existing_term

    @override
    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        try:
            path = PurePosixPath("input") / "bindingconstraints" / f"{constraint.id}_{matrix_name.value}"
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise ConstraintMatrixDownloadError(constraint.id, matrix_name.value, e.message) from e

    @override
    def set_constraint_matrix(
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

    @override
    def add_constraint_terms(self, constraint: BindingConstraint, terms: list[ConstraintTerm]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint.id}"
        try:
            json_terms = [{"weight": term.weight, "offset": term.offset, "data": asdict(term.data)} for term in terms]
            self._wrapper.post(f"{url}/terms", json=json_terms)

        except APIError as e:
            raise ConstraintTermAdditionError(constraint.id, [term.id for term in terms], e.message) from e

    @override
    def read_binding_constraints(self) -> dict[str, BindingConstraint]:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints"
        try:
            response = self._wrapper.get(url)
            constraints_json = response.json()
            constraints: dict[str, BindingConstraint] = {}

            for constraint in constraints_json:
                constraint_name = constraint.pop("name")
                del constraint["id"]
                api_terms = constraint.pop("terms")
                api_properties = BindingConstraintPropertiesAPI.model_validate(constraint)
                bc_properties = api_properties.to_user_model()
                terms: list[ConstraintTerm] = []
                for api_term in api_terms:
                    term_data = ConstraintTermData.from_dict(api_term["data"])
                    terms.append(ConstraintTerm(weight=api_term["weight"], offset=api_term["offset"], data=term_data))
                bc = BindingConstraint(constraint_name, self, bc_properties, terms)
                constraints[bc.id] = bc

            return constraints
        except APIError as e:
            raise ConstraintRetrievalError(self.study_id, e.message) from e

    @override
    def update_binding_constraints_properties(
        self, new_properties: dict[str, BindingConstraintPropertiesUpdate]
    ) -> dict[str, BindingConstraintProperties]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/binding-constraints"
        body = {}
        updated_constraints: dict[str, BindingConstraintProperties] = {}

        for bc_id, props in new_properties.items():
            api_properties = BindingConstraintPropertiesAPI.from_user_model(props)
            api_dict = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            body[bc_id] = api_dict

        try:
            binding_constraints_dict = self._wrapper.put(url, json=body).json()

            for binding_constraint, props in binding_constraints_dict.items():
                api_response = BindingConstraintPropertiesAPI.model_validate(props)
                constraints_properties = api_response.to_user_model()
                updated_constraints[binding_constraint] = constraints_properties

        except APIError as e:
            raise ConstraintsPropertiesUpdateError(self.study_id, e.message) from e

        return updated_constraints
