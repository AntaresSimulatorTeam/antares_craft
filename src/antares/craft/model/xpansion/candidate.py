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


from dataclasses import asdict, dataclass
from typing import Optional

from antares.craft.exceptions.exceptions import BadCandidateFormatError
from antares.craft.tools.contents_tool import EnumIgnoreCase


class XpansionLinkProfile(EnumIgnoreCase):
    DIRECT_LINK = "direct-link-profile"
    INDIRECT_LINK = "indirect-link-profile"
    ALREADY_INSTALLED_DIRECT_LINK = "already-installed-direct-link-profile"
    ALREADY_INSTALLED_INDIRECT_LINK = "already-installed-indirect-link-profile"


@dataclass(frozen=True)
class XpansionCandidate:
    name: str
    area_from: str
    area_to: str
    annual_cost_per_mw: float
    already_installed_capacity: Optional[int] = None
    unit_size: Optional[float] = None
    max_units: Optional[int] = None
    max_investment: Optional[float] = None
    direct_link_profile: Optional[str] = None
    indirect_link_profile: Optional[str] = None
    already_installed_direct_link_profile: Optional[str] = None
    already_installed_indirect_link_profile: Optional[str] = None

    def __post_init__(self) -> None:
        if self.max_investment is None and (self.unit_size is None or self.max_units is None):
            raise BadCandidateFormatError(self.name)


@dataclass
class XpansionCandidateUpdate:
    name: Optional[str] = None
    area_from: Optional[str] = None
    area_to: Optional[str] = None
    annual_cost_per_mw: Optional[float] = None
    already_installed_capacity: Optional[int] = None
    unit_size: Optional[float] = None
    max_units: Optional[int] = None
    max_investment: Optional[float] = None
    direct_link_profile: Optional[str] = None
    indirect_link_profile: Optional[str] = None
    already_installed_direct_link_profile: Optional[str] = None
    already_installed_indirect_link_profile: Optional[str] = None


def update_candidate(candidate: XpansionCandidate, candidate_update: XpansionCandidateUpdate) -> XpansionCandidate:
    candidate_dict = asdict(candidate)
    candidate_dict.update({k: v for k, v in asdict(candidate_update).items() if v is not None})
    return XpansionCandidate(**candidate_dict)
