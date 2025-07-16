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

from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.service.base_services import BaseXpansionService


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
