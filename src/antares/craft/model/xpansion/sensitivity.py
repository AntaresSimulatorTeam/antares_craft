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

from dataclasses import dataclass
from typing import Optional


@dataclass(frozen=True)
class XpansionSensitivity:
    epsilon: float
    projection: list[str]
    capex: bool


@dataclass
class XpansionSensitivityUpdate:
    epsilon: Optional[float] = None
    projection: Optional[list[str]] = None
    capex: Optional[bool] = None
