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

from enum import Enum
from typing import Any, Dict, List, Optional, Union

import pandas as pd

from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id
from pydantic import BaseModel, Field, model_validator
from pydantic.alias_generators import to_camel


class BindingConstraintFrequency(EnumIgnoreCase):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(EnumIgnoreCase):
    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


class ConstraintMatrixName(Enum):
    LESS_TERM = "lt"
    EQUAL_TERM = "eq"
    GREATER_TERM = "gt"


class TermOperators(BaseModel):
    weight: Optional[float] = None
    offset: Optional[int] = None

    def weight_offset(self) -> str:
        if self.offset is not None:
            # Rounded the weight to 6 decimals to be in line with other floats in the ini files
            weight_offset = f"{(self.weight if self.weight is not None else 0):.6f}%{self.offset}"
        else:
            weight_offset = f"{self.weight if self.weight is not None else 0}"
        return weight_offset


class LinkData(BaseModel):
    """
    DTO for a constraint term on a link between two areas.
    """

    area1: str
    area2: str


class ClusterData(BaseModel):
    """
    DTO for a constraint term on a cluster in an area.
    """

    area: str
    cluster: str


class ConstraintTerm(TermOperators):
    data: Union[LinkData, ClusterData]
    id: str = Field(init=False)

    @model_validator(mode="before")
    def fill_id(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        v["id"] = cls.generate_id(v["data"])
        return v

    @classmethod
    def generate_id(cls, data: Union[Dict[str, str], LinkData, ClusterData]) -> str:
        if isinstance(data, dict):
            if "area1" in data:
                return "%".join(sorted((data["area1"].lower(), data["area2"].lower())))
            return ".".join((data["area"].lower(), data["cluster"].lower()))
        elif isinstance(data, LinkData):
            return "%".join(sorted((data.area1.lower(), data.area2.lower())))
        return ".".join((data.area.lower(), data.cluster.lower()))


class DefaultBindingConstraintProperties(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    """Default properties for binding constraints

    Attributes:
        enabled (bool): True
        time_step (BindingConstraintFrequency): BindingConstraintFrequency.HOURLY
        operator (BindingConstraintOperator): BindingConstraintOperator.LESS
        comments (str): None
        filter_year_by_year (str): "hourly"
        filter_synthesis (str): "hourly"
        group (str): "default"

    """

    enabled: bool = True
    time_step: BindingConstraintFrequency = BindingConstraintFrequency.HOURLY
    operator: BindingConstraintOperator = BindingConstraintOperator.LESS
    comments: str = ""
    filter_year_by_year: str = "hourly"
    filter_synthesis: str = "hourly"
    group: str = "default"


@all_optional_model
class BindingConstraintProperties(DefaultBindingConstraintProperties):
    pass


class BindingConstraint:
    def __init__(  # type: ignore # TODO: Find a way to avoid circular imports
        self,
        name: str,
        binding_constraint_service,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[List[ConstraintTerm]] = None,
    ):
        self._name = name
        self._binding_constraint_service = binding_constraint_service
        self._id = transform_name_to_id(name)
        self._properties = properties or BindingConstraintProperties()
        self._terms = {term.id: term for term in terms} if terms else {}

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def properties(self) -> BindingConstraintProperties:
        return self._properties

    @properties.setter
    def properties(self, new_properties: BindingConstraintProperties) -> None:
        self._properties = new_properties

    def get_terms(self) -> Dict[str, ConstraintTerm]:
        return self._terms

    def add_terms(self, terms: List[ConstraintTerm]) -> None:
        added_terms = self._binding_constraint_service.add_constraint_terms(self, terms)
        for term in added_terms:
            self._terms[term.id] = term

    def delete_term(self, term: ConstraintTerm) -> None:
        self._binding_constraint_service.delete_binding_constraint_term(self.id, term.id)
        self._terms.pop(term.id)

    def update_properties(self, properties: BindingConstraintProperties) -> None:
        new_properties = self._binding_constraint_service.update_binding_constraint_properties(self, properties)
        self._properties = new_properties

    def get_less_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.LESS_TERM)

    def get_equal_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM)

    def get_greater_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM)

    def update_less_term_matrix(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.update_constraint_matrix(self, ConstraintMatrixName.LESS_TERM, matrix)

    def update_equal_term_matrix(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.update_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM, matrix)

    def update_greater_term_matrix(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.update_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM, matrix)
