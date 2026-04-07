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
from typing import Optional

import pandas as pd

from antares.craft.model.commons import FilterOption
from antares.craft.service.base_services import BaseBindingConstraintService
from antares.craft.tools.contents_tool import EnumIgnoreCase
from antares.craft.tools.utils import FILTER_VALUES, ConstraintMatrixName


class BindingConstraintFrequency(EnumIgnoreCase):
    """An enumeration representing the possible frequencies for binding constraints.

    The values are case-insensitive, so "HOURLY", "hourly", or "Hourly" are all valid.

    Attributes:
        HOURLY: Constraints are applied every hour.
        DAILY: Constraints are applied every day.
        WEEKLY: Constraints are applied every week.
    """

    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"


class BindingConstraintOperator(EnumIgnoreCase):
    """An enumeration representing the possible operators for binding constraints.

    The values are case-insensitive, so "LESS", "less", or "Less" are all valid.

    Attributes:
        LESS: Represents a "less than" (<) constraint.
        GREATER: Represents a "greater than" (>) constraint.
        BOTH: Represents a "both less than and greater than" constraint.
        EQUAL: Represents an "equal to" (==) constraint.
    """

    LESS = "less"
    GREATER = "greater"
    BOTH = "both"
    EQUAL = "equal"


@dataclass(frozen=True)
class LinkData:
    """Data Transfer Object (DTO) for a constraint term on a link between two areas.

    Attributes:
        area1: The first area
        area2: The second area
    """

    area1: str
    area2: str


@dataclass(frozen=True)
class ClusterData:
    """Data Transfer Object (DTO) for a constraint term on a cluster in an area.

    Attributes:
        area: The area
        cluster: The cluster
    """

    area: str
    cluster: str


@dataclass(frozen=True)
class ConstraintTermData:
    """Constraint term in the left hand side of a binding constraint.

    Attributes:
        data: The underlying data, which can be either a `LinkData` or `ClusterData` object.
    """

    data: LinkData | ClusterData

    @property
    def id(self) -> str:
        """Generate a unique string identifier for the constraint term
        - For a link term type: "area1%area2" (sorted alphabetically and lowercase)
        - For a cluster term type: "area.cluster" (lowercase)
        """
        if isinstance(self.data, LinkData):
            return "%".join(sorted((self.data.area1.lower(), self.data.area2.lower())))
        return ".".join((self.data.area.lower(), self.data.cluster.lower()))

    @staticmethod
    def from_dict(input: dict[str, str]) -> LinkData | ClusterData:
        """Create a `LinkData` or `ClusterData` object from a dictionary.

        Args:
            input: A dictionary containing either "area1" and "area2" keys (for `LinkData`)
                   or "area" and "cluster" keys (for `ClusterData`).

        Returns:
            LinkData | ClusterData: An instance of `LinkData` or `ClusterData` based on the input.

        Raises:
            ValueError: If the dictionary does not contain the required keys.
        """
        if "area1" in input:
            return LinkData(area1=input["area1"], area2=input["area2"])
        elif "cluster" in input:
            return ClusterData(area=input["area"], cluster=input["cluster"])
        raise ValueError(f"Dict {input} couldn't be serialized as a ConstraintTermData object")

    @staticmethod
    def from_ini(input: str) -> LinkData | ClusterData:
        """Creates a `LinkData` or `ClusterData` object from a string.

        Args:
            input: A string formatted as "area1%area2" (for `LinkData`) or "area.cluster" (for `ClusterData`).

        Returns:
            An instance of `LinkData` or `ClusterData` based on the input.

        Raises:
            ValueError: If the string does not match the expected format.
        """
        if "%" in input:
            area_1, area_2 = input.split("%")
            return LinkData(area1=area_1, area2=area_2)
        elif "." in input:
            area, cluster = input.split(".")
            return ClusterData(area=area, cluster=cluster)
        raise ValueError(f"Input {input} couldn't be serialized as a ConstraintTermData object")


@dataclass(frozen=True)
class ConstraintTerm(ConstraintTermData):
    """Constraint terms

    Attributes:
        weigth:
            The coefficient multiplying the link or cluster
        offset:
            The time offset of flow on the given link or output of the cluster.
            For example, it allows to make a constraint on a previous time-step.
    """

    weight: float = 1
    offset: int = 0

    def weight_offset(self) -> str:
        """Format the weight and offset values into a string representation."""
        return f"{self.weight}%{self.offset}" if self.offset != 0 else f"{self.weight}"


@dataclass
class BindingConstraintPropertiesUpdate:
    """Update binding constraint properties

    Attributes:
        enabled: Whether or not the binding constraint is enabled for the simulation.
        time_step: Frequency at which the binding constraint is applied.
        operator: Bound of the bounding constraint (<, >, == or < and >).
        comments: User comments on the constraint.
        filter_year_by_year: Set of filter options for output (hourly, daily, weekly, monthly, annual).
        filter_synthesis: Set of filter options for synthesis (hourly, daily, weekly, monthly, annual).
        group: User defined group to organize binding constraints
    """

    enabled: Optional[bool] = None
    time_step: Optional[BindingConstraintFrequency] = None
    operator: Optional[BindingConstraintOperator] = None
    comments: Optional[str] = None
    filter_year_by_year: Optional[set[FilterOption]] = None
    filter_synthesis: Optional[set[FilterOption]] = None
    group: Optional[str] = None


@dataclass(frozen=True)
class BindingConstraintProperties:
    """Binding constraint properties

    Attributes:
        enabled: Whether or not the binding constraint is enabled for the simulation.
        time_step: Frequency at which the binding constraint is applied.
        operator: Bound of the bounding constraint (<, >, == or < and >).
        comments: User comments on the constraint.
        filter_year_by_year: Set of filter options for output (hourly, daily, weekly, monthly, annual).
        filter_synthesis: Set of filter options for synthesis (hourly, daily, weekly, monthly, annual).
        group: User defined group to organize binding constraints
    """

    enabled: bool = True
    time_step: BindingConstraintFrequency = BindingConstraintFrequency.HOURLY
    operator: BindingConstraintOperator = BindingConstraintOperator.LESS
    comments: str = ""
    filter_year_by_year: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    filter_synthesis: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    group: str = "default"


class BindingConstraint:
    """Define generic constraints (binding constraints) between transmission flows
    and/or power generated from thermal clusters.
    """

    def __init__(
        self,
        bc_id: str,
        name: str,
        binding_constraint_service: BaseBindingConstraintService,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[list[ConstraintTerm]] = None,
    ):
        self._name = name
        self._binding_constraint_service = binding_constraint_service
        self._id = bc_id
        self._properties = properties or BindingConstraintProperties()
        self._terms = {term.id: term for term in terms} if terms else {}

    @property
    def name(self) -> str:
        """Name of the constraint."""
        return self._name

    @property
    def id(self) -> str:
        """ID of the constraint."""
        return self._id

    @property
    def properties(self) -> BindingConstraintProperties:
        """Binding constraints properties"""
        return self._properties

    def get_terms(self) -> dict[str, ConstraintTerm]:
        """Get the terms of this binding constraint.

        Returns:
            The constraint terms, as a mapping of term ID to term.
        """
        return self._terms

    def set_terms(self, terms: list[ConstraintTerm]) -> None:
        """Replace all terms of this binding constraint.

        Args:
            terms: The new list of constraint terms to set.
        """
        self._binding_constraint_service.set_constraint_terms(self, terms)
        new_terms = {term.id: term for term in terms}
        self._terms = new_terms

    def update_properties(self, properties: BindingConstraintPropertiesUpdate) -> BindingConstraintProperties:
        """Update properties of the binding constraint."""
        new_properties = self._binding_constraint_service.update_binding_constraints_properties({self.id: properties})
        self._properties = new_properties[self.id]
        return self._properties

    def get_less_term_matrix(self) -> pd.DataFrame:
        """Get the "less than" (<) term matrix"""
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.LESS_TERM)

    def get_equal_term_matrix(self) -> pd.DataFrame:
        """Get the "equal" (==) term matrix"""
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM)

    def get_greater_term_matrix(self) -> pd.DataFrame:
        """Get the "greater than" (>) term matrix"""
        return self._binding_constraint_service.get_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM)

    def set_less_term(self, matrix: pd.DataFrame) -> None:
        """Set the "less than" (<) term matrix

        Args:
            matrix: the matrix to upload.
        """
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.LESS_TERM, matrix)

    def set_equal_term(self, matrix: pd.DataFrame) -> None:
        """Set the "equal" (==) term matrix

        Args:
            matrix: the matrix to upload.
        """
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.EQUAL_TERM, matrix)

    def set_greater_term(self, matrix: pd.DataFrame) -> None:
        """Set the "greater than" (>) term matrix

        Args:
            matrix: the matrix to upload.
        """
        self._binding_constraint_service.set_constraint_matrix(self, ConstraintMatrixName.GREATER_TERM, matrix)
