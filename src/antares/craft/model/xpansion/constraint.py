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

from antares.craft.tools.contents_tool import EnumIgnoreCase


class ConstraintSign(EnumIgnoreCase):
    LESS_OR_EQUAL = "less_or_equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    EQUAL = "equal"


@dataclass(frozen=True)
class XpansionConstraint:
    name: str
    sign: ConstraintSign
    right_hand_side: float
    candidates_coefficients: dict[str, float] = field(default_factory=dict)


@dataclass
class XpansionConstraintUpdate:
    name: Optional[str] = None
    sign: Optional[ConstraintSign] = None
    right_hand_side: Optional[float] = None
    candidates_coefficients: Optional[dict[str, float]] = None
