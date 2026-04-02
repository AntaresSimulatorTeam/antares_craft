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


@dataclass(frozen=True)
class XpansionSensitivity:
    """Xpansion sensitivity parameters.
    
    Attributes:
        epsilon: Maximum allowed gap with the optimal solution
        projection: List of candidate names for which min/max investment in near optimal solution will be looked for
        capex: Whether or not to look for solution with min/max CAPEX
    """
    epsilon: float = 0
    projection: list[str] = field(default_factory=list)
    capex: bool = False


@dataclass
class XpansionSensitivityUpdate:
    """Xpansion sensitivity parameter update.
    
    Attributes:
        epsilon: Maximum allowed gap with the optimal solution
        projection: List of candidate names for which min/max investment in near optimal solution will be looked for
        capex: Whether or not to look for solution with min/max CAPEX
    """
    epsilon: Optional[float] = None
    projection: Optional[list[str]] = None
    capex: Optional[bool] = None


def update_xpansion_sensitivity(
    sensitivity: XpansionSensitivity, sensitivity_update: XpansionSensitivityUpdate
) -> XpansionSensitivity:
    """Update Xpansion sensitivity parameters.
    
    Args:
        sensitivity: The Xpansion sensitivity parameters.
        sensitivity_update: The parameters to update and their values.

    Returns:
        The updated Xpansion sensivity parameters.
    """
    sensitivity_dict = asdict(sensitivity)
    update_dict = {k: v for k, v in asdict(sensitivity_update).items() if v is not None}
    sensitivity_dict.update(update_dict)

    return XpansionSensitivity(**sensitivity_dict)
