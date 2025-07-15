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

from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings


@dataclass
class XpansionConfiguration:
    settings: XpansionSettings
    candidates: dict[str, XpansionCandidate] = field(default_factory=dict)
    constraints: dict[str, XpansionConstraint] = field(default_factory=dict)
    sensitivity: dict[str, XpansionSensitivity] = field(default_factory=dict)
