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
from types import MappingProxyType
from typing import Optional

import pandas as pd

from antares.craft.model.xpansion.candidate import XpansionCandidate, XpansionCandidateUpdate, XpansionLinkProfile
from antares.craft.model.xpansion.constraint import XpansionConstraint, XpansionConstraintUpdate
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.service.base_services import BaseXpansionService
from antares.craft.tools.contents_tool import EnumIgnoreCase


class XpansionMatrix(EnumIgnoreCase):
    CAPACITIES = "capacities"
    WEIGHTS = "weights"


class XpansionConfiguration:
    def __init__(
        self,
        xpansion_service: BaseXpansionService,
        settings: XpansionSettings,
        candidates: Optional[dict[str, XpansionCandidate]] = None,
        constraints: Optional[dict[str, XpansionConstraint]] = None,
        sensitivity: Optional[XpansionSensitivity] = None,
    ):
        self._settings = settings
        self._candidates = candidates or {}
        self._constraints = constraints or {}
        self._sensitivity = sensitivity
        self._xpansion_service = xpansion_service

    @property
    def settings(self) -> XpansionSettings:
        return self._settings

    @property
    def sensitivity(self) -> XpansionSensitivity | None:
        return self._sensitivity

    def get_candidates(self) -> MappingProxyType[str, XpansionCandidate]:
        return MappingProxyType(self._candidates)

    def get_constraints(self) -> MappingProxyType[str, XpansionConstraint]:
        return MappingProxyType(self._constraints)

    def get_capacity(self, file_name: str) -> pd.DataFrame:
        return self._xpansion_service.get_matrix(file_name, XpansionMatrix.CAPACITIES)

    def get_weight(self, file_name: str) -> pd.DataFrame:
        return self._xpansion_service.get_matrix(file_name, XpansionMatrix.WEIGHTS)

    def delete_capacity(self, file_name: str) -> None:
        return self._xpansion_service.delete_matrix(file_name, XpansionMatrix.CAPACITIES)

    def delete_weight(self, file_name: str) -> None:
        return self._xpansion_service.delete_matrix(file_name, XpansionMatrix.WEIGHTS)

    def set_capacity(self, file_name: str, series: pd.DataFrame) -> None:
        return self._xpansion_service.set_matrix(file_name, series, XpansionMatrix.CAPACITIES)

    def set_weight(self, file_name: str, series: pd.DataFrame) -> None:
        return self._xpansion_service.set_matrix(file_name, series, XpansionMatrix.WEIGHTS)

    def create_candidate(self, candidate: XpansionCandidate) -> XpansionCandidate:
        cdt = self._xpansion_service.create_candidate(candidate)
        self._candidates[cdt.name] = cdt
        return cdt

    def update_candidate(self, candidate_name: str, candidate: XpansionCandidateUpdate) -> XpansionCandidate:
        cdt = self._xpansion_service.update_candidate(candidate_name, candidate)
        if cdt.name not in self._candidates:
            # Means we're renaming a candidate (+ updating it)
            del self._candidates[candidate_name]

        self._candidates[cdt.name] = cdt
        return cdt

    def delete_candidates(self, names: list[str]) -> None:
        self._xpansion_service.delete_candidates(set(names))
        for name in names:
            del self._candidates[name]

    def remove_links_profile_from_candidate(self, name: str, profiles: list[XpansionLinkProfile]) -> None:
        current_candidate = self._candidates[name]
        new_candidate = self._xpansion_service.remove_links_profile_from_candidate(current_candidate, profiles)
        self._candidates[name] = new_candidate

    def create_constraint(self, constraint: XpansionConstraint, file_name: str) -> XpansionConstraint:
        constraint = self._xpansion_service.create_constraint(constraint, file_name)
        self._constraints[constraint.name] = constraint
        return constraint

    def update_constraint(self, name: str, constraint: XpansionConstraintUpdate, file_name: str) -> XpansionConstraint:
        new_constraint = self._xpansion_service.update_constraint(name, constraint, file_name)
        if new_constraint.name != name:
            # We're renaming a constraint
            del self._constraints[name]
        self._constraints[new_constraint.name] = new_constraint
        return new_constraint

    def delete_constraints(self, names: list[str], file_name: str) -> None:
        self._xpansion_service.delete_constraints(names, file_name)
        for name in names:
            del self._constraints[name]

    def delete_constraints_file(self, file_name: str) -> None:
        self._xpansion_service.delete_constraints_file(file_name)
