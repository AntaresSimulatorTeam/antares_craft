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

from antares.craft.tools.contents_tool import EnumIgnoreCase


class UcType(EnumIgnoreCase):
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(EnumIgnoreCase):
    INTEGER = "integer"
    RELAXED = "relaxed"


class XpansionSolver(EnumIgnoreCase):
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


@dataclass(frozen=True)
class XpansionSettings:
    master: Master = Master.INTEGER
    uc_type: UcType = UcType.EXPANSION_FAST
    optimality_gap: float = 1
    relative_gap: float = 1e-6
    relaxed_optimality_gap: float = 1e-5
    max_iteration: int = 1000
    solver: XpansionSolver = XpansionSolver.XPRESS
    log_level: int = 0
    separation_parameter: float = 0.5
    batch_size: int = 96
    yearly_weights: Optional[str] = None
    additional_constraints: Optional[str] = None
    timelimit: int = int(1e12)


@dataclass
class XpansionSettingsUpdate:
    master: Optional[Master] = None
    uc_type: Optional[UcType] = None
    optimality_gap: Optional[float] = None
    relative_gap: Optional[float] = None
    relaxed_optimality_gap: Optional[float] = None
    max_iteration: Optional[int] = None
    solver: Optional[XpansionSolver] = None
    log_level: Optional[int] = None
    separation_parameter: Optional[float] = None
    batch_size: Optional[int] = None
    yearly_weights: Optional[str] = None
    additional_constraints: Optional[str] = None
    timelimit: Optional[int] = None


def update_xpansion_settings(settings: XpansionSettings, settings_update: XpansionSettingsUpdate) -> XpansionSettings:
    settings_dict = asdict(settings)
    update_dict = {k: v for k, v in asdict(settings_update).items() if v is not None}
    settings_dict.update(update_dict)

    return XpansionSettings(**settings_dict)
