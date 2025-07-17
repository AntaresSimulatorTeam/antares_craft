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
from dataclasses import replace
from types import MappingProxyType
from typing import Optional

import pandas as pd

from antares.craft.model.xpansion.candidate import XpansionCandidate, XpansionCandidateUpdate, XpansionLinkProfile
from antares.craft.model.xpansion.constraint import XpansionConstraint
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

    def remove_links_profile_from_candidate(self, name: str, profiles: list[XpansionLinkProfile]) -> None:
        self._xpansion_service.remove_links_profile_from_candidate(name, profiles)
        candidate = self._candidates[name]
        for profile in profiles:
            if profile == XpansionLinkProfile.DIRECT_LINK:
                candidate = replace(candidate, direct_link_profile=None)
            elif profile == XpansionLinkProfile.INDIRECT_LINK:
                candidate = replace(candidate, indirect_link_profile=None)
            elif profile == XpansionLinkProfile.ALREADY_INSTALLED_DIRECT_LINK:
                candidate = replace(candidate, already_installed_direct_link_profile=None)
            else:
                candidate = replace(candidate, already_installed_indirect_link_profile=None)
        self._candidates[name] = candidate
