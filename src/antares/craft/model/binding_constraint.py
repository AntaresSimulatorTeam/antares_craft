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
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd

from antares.craft.model.commons import FILTER_VALUES, FilterOption
from antares.craft.service.base_services import BaseBindingConstraintService
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id


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


@dataclass(frozen=True)
class LinkData:
    """
    DTO for a constraint term on a link between two areas.
    """

    area1: str
    area2: str


@dataclass(frozen=True)
class ClusterData:
    """
    DTO for a constraint term on a cluster in an area.
    """

    area: str
    cluster: str


@dataclass(frozen=True)
class ConstraintTermData:
    data: LinkData | ClusterData

    @property
    def id(self) -> str:
        if isinstance(self.data, LinkData):
            return "%".join(sorted((self.data.area1.lower(), self.data.area2.lower())))
        return ".".join((self.data.area.lower(), self.data.cluster.lower()))

    @staticmethod
    def from_dict(input: dict[str, str]) -> LinkData | ClusterData:
        if "area1" in input:
            return LinkData(area1=input["area1"], area2=input["area2"])
        elif "cluster" in input:
            return ClusterData(area=input["area"], cluster=input["cluster"])
        raise ValueError(f"Dict {input} couldn't be serialized as a ConstraintTermData object")

    @staticmethod
    def from_ini(input: str) -> LinkData | ClusterData:
        if "%" in input:
            area_1, area_2 = input.split("%")
            return LinkData(area1=area_1, area2=area_2)
        elif "." in input:
            area, cluster = input.split(".")
            return ClusterData(area=area, cluster=cluster)
        raise ValueError(f"Input {input} couldn't be serialized as a ConstraintTermData object")


@dataclass(frozen=True)
class ConstraintTermUpdate(ConstraintTermData):
    weight: Optional[float] = None
    offset: Optional[int] = None


@dataclass(frozen=True)
class ConstraintTerm(ConstraintTermData):
    weight: float = 1
    offset: int = 0

    def weight_offset(self) -> str:
        return f"{self.weight}%{self.offset}" if self.offset != 0 else f"{self.weight}"


@dataclass
class BindingConstraintPropertiesUpdate:
    enabled: Optional[bool] = None
    time_step: Optional[BindingConstraintFrequency] = None
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None
    filter_year_by_year: Optional[set[FilterOption]] = None
    filter_synthesis: Optional[set[FilterOption]] = None
    group: Optional[str] = None


@dataclass(frozen=True)
class BindingConstraintProperties:
    enabled: bool = True
    time_step: BindingConstraintFrequency = BindingConstraintFrequency.HOURLY
    operator: BindingConstraintOperator = BindingConstraintOperator.LESS
    comments: str = ""
    filter_year_by_year: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    filter_synthesis: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    group: str = "default"


class BindingConstraint:
    def __init__(
        self,
        name: str,
        binding_constraint_service: BaseBindingConstraintService,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[list[ConstraintTerm]] = None,
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

    def get_terms(self) -> dict[str, ConstraintTerm]:
        return self._terms

    def add_terms(self, terms: list[ConstraintTerm]) -> None:
        self._binding_constraint_service.add_constraint_terms(self, terms)
        for term in terms:
            self._terms[term.id] = term

    def delete_term(self, term: ConstraintTerm) -> None:
        self._binding_constraint_service.delete_binding_constraint_term(self.id, term.id)
        self._terms.pop(term.id)

    def update_term(self, term: ConstraintTermUpdate) -> None:
        existing_term = self._terms[term.id]
        new_term = self._binding_constraint_service.update_binding_constraint_term(self.id, term, existing_term)
        self._terms[term.id] = new_term

    def update_properties(self, properties: BindingConstraintPropertiesUpdate) -> BindingConstraintProperties:
        new_properties = self._binding_constraint_service.update_binding_constraints_properties({self.id: properties})
        self._properties = new_properties[self.id]
        return self._properties

    def get_less_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.LESS_TERM)

    def get_equal_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM)

    def get_greater_term_matrix(self) -> pd.DataFrame:
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM)

    def set_less_term(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.LESS_TERM, matrix)

    def set_equal_term(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM, matrix)

    def set_greater_term(self, matrix: pd.DataFrame) -> None:
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM, matrix)
