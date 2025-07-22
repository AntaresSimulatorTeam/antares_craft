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

from antares.craft.exceptions.exceptions import (
    XpansionCandidateDeletionError,
    XpansionCandidateEditionError,
    XpansionResourceDeletionError,
    XpansionSensitivityEditionError,
)
from antares.craft.model.xpansion.candidate import XpansionCandidate, XpansionCandidateUpdate, XpansionLinkProfile
from antares.craft.model.xpansion.constraint import XpansionConstraint, XpansionConstraintUpdate
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity, XpansionSensitivityUpdate
from antares.craft.model.xpansion.settings import XpansionSettings, XpansionSettingsUpdate
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
        sensitivity: XpansionSensitivity,
        candidates: Optional[dict[str, XpansionCandidate]] = None,
        constraints: Optional[dict[str, XpansionConstraint]] = None,
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
    def sensitivity(self) -> XpansionSensitivity:
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
        # Checks the capacity file is not referenced in a candidate
        for candidate in self._candidates.values():
            for profile in [
                "direct_link_profile",
                "indirect_link_profile",
                "already_installed_direct_link_profile",
                "already_installed_indirect_link_profile",
            ]:
                if file_name == getattr(candidate, profile):
                    raise XpansionResourceDeletionError(
                        "capacity", file_name, f"It is referenced in the candidate {candidate.name}"
                    )

        return self._xpansion_service.delete_matrix(file_name, XpansionMatrix.CAPACITIES)

    def delete_weight(self, file_name: str) -> None:
        # Checks the weight file is not referenced in the settings
        if self._settings.yearly_weights == file_name:
            raise XpansionResourceDeletionError("weight", file_name, "It is referenced in the settings")

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
        if candidate.name and candidate.name != candidate_name:
            # Means we're renaming a candidate
            # We have to check it wasn't referenced inside the sensitivity config
            if candidate_name in self._sensitivity.projection:
                raise XpansionCandidateEditionError(
                    self._xpansion_service.study_id, candidate_name, "It is referenced in the sensitivity config"
                )

        cdt = self._xpansion_service.update_candidate(candidate_name, candidate)
        if cdt.name not in self._candidates:
            # Means we're renaming a candidate (+ updating it)
            del self._candidates[candidate_name]

        self._candidates[cdt.name] = cdt
        return cdt

    def delete_candidates(self, names: list[str]) -> None:
        # Checks the candidates are not referenced inside the sensitivity config
        problematic_candidates = set()
        for name in names:
            if name in set(self._sensitivity.projection):
                problematic_candidates.add(name)
        if problematic_candidates:
            raise XpansionCandidateDeletionError(
                self._xpansion_service.study_id, problematic_candidates, "They are referenced in the sensitivity config"
            )
        # Performs the deletion
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
        # Checks the constraint file is not referenced in the settings
        if self._settings.additional_constraints == file_name:
            raise XpansionResourceDeletionError("constraints", file_name, "It is referenced in the settings")
        self._xpansion_service.delete_constraints_file(file_name)

    def update_settings(self, settings: XpansionSettingsUpdate) -> XpansionSettings:
        new_settings = self._xpansion_service.update_settings(settings, self._settings)
        self._settings = new_settings
        return new_settings

    def remove_constraints_and_or_weights_from_settings(self, constraint: bool, weight: bool) -> None:
        if not constraint and not weight:
            return
        new_settings = self._xpansion_service.remove_constraints_and_or_weights_from_settings(
            constraint, weight, self._settings
        )
        self._settings = new_settings

    def update_sensitivity(self, sensitivity: XpansionSensitivityUpdate) -> XpansionSensitivity:
        # Ensures projections correspond to existing candidates
        if sensitivity.projection:
            problematic_candidates = set()
            for name in sensitivity.projection:
                if name not in self._candidates:
                    problematic_candidates.add(name)
            if problematic_candidates:
                raise XpansionSensitivityEditionError(
                    self._xpansion_service.study_id, f"The candidates {problematic_candidates} do not exist"
                )
        # Performs the update
        new_sensitivity = self._xpansion_service.update_sensitivity(sensitivity, self._settings, self._sensitivity)
        self._sensitivity = new_sensitivity
        return new_sensitivity
