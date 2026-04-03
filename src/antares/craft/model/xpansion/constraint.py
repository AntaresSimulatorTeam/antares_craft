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


from dataclasses import asdict, dataclass, field
from typing import Optional

from antares.craft.tools.contents_tool import EnumIgnoreCase


class ConstraintSign(EnumIgnoreCase):
    """Constraint available signs.

    Attributes:
        LESS_OR_EQUAL: "<="
        GREATER_OR_EQUAL: ">="
        EQUAL: "=="
    """

    LESS_OR_EQUAL = "less_or_equal"
    GREATER_OR_EQUAL = "greater_or_equal"
    EQUAL = "equal"


@dataclass(frozen=True)
class XpansionConstraint:
    """Represents a linear constraint between invested capacities of Xpansion candidates.

    Attributes:
        name: Name of the constraint.
        sign: Sign of the constraint (`LESS_OR_EQUAL`, `GREATER_OR_EQUAL` or `EQUAL`).
        right_hand_side: Right-hand side of the constraint.
        candidates_coefficients: Coefficients of candidate investments in the constraint.
    """

    name: str
    sign: ConstraintSign
    right_hand_side: float
    candidates_coefficients: dict[str, float] = field(default_factory=dict)


@dataclass
class XpansionConstraintUpdate:
    """Update of a linear constraint between invested capacities of Xpansion candidates.

    Attributes:
        name: Name of the constraint.
        sign: Sign of the constraint (`LESS_OR_EQUAL`, `GREATER_OR_EQUAL` or `EQUAL`).
        right_hand_side: Right-hand side of the constraint.
        candidates_coefficients: Coefficients of candidate investments in the constraint.
    """

    name: Optional[str] = None
    sign: Optional[ConstraintSign] = None
    right_hand_side: Optional[float] = None
    candidates_coefficients: Optional[dict[str, float]] = None


def update_constraint(
    constraint: XpansionConstraint, constraint_update: XpansionConstraintUpdate
) -> XpansionConstraint:
    """Update a Xpansion constraint.

    Args:
        constraint: The original constraint.
        constraint_update: The updated fields to apply on `constraint`.

    Returns:
        The updated constraint.
    """
    constraint_dict = asdict(constraint)
    update_dict = {k: v for k, v in asdict(constraint_update).items() if v is not None}

    constraint_dict["candidates_coefficients"].update(update_dict.pop("candidates_coefficients", {}))
    constraint_dict.update(update_dict)

    return XpansionConstraint(**constraint_dict)
