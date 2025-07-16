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
from dataclasses import asdict
from typing import Any, Optional

from pydantic import Field

from antares.craft.model.xpansion.settings import Master, Solver, UcType, XpansionSettings, XpansionSettingsUpdate
from antares.craft.service.local_services.models.base_model import LocalBaseModel

XpansionSettingsType = XpansionSettings | XpansionSettingsUpdate


class XpansionSettingsLocal(LocalBaseModel):
    master: Master = Master.INTEGER
    uc_type: UcType = UcType.EXPANSION_FAST
    optimality_gap: float = 1
    relative_gap: float = 1e-6
    relaxed_optimality_gap: float = 1e-5
    max_iteration: int = 1000
    solver: Solver = Solver.XPRESS
    log_level: int = 0
    separation_parameter: float = 0.5
    batch_size: int = 96
    yearly_weights: Optional[str] = Field(None, alias="yearly-weights")
    additional_constraints: Optional[str] = Field(None, alias="additional-constraints")
    timelimit: int = int(1e12)

    @staticmethod
    def from_user_model(user_class: XpansionSettingsType) -> "XpansionSettingsLocal":
        user_dict = asdict(user_class)
        return XpansionSettingsLocal.model_validate(user_dict)

    def to_user_model(self) -> XpansionSettings:
        return XpansionSettings(
            master=self.master,
            uc_type=self.uc_type,
            optimality_gap=self.optimality_gap,
            relative_gap=self.relative_gap,
            relaxed_optimality_gap=self.relaxed_optimality_gap,
            max_iteration=self.max_iteration,
            solver=self.solver,
            log_level=self.log_level,
            separation_parameter=self.separation_parameter,
            batch_size=self.batch_size,
            yearly_weights=self.yearly_weights,
            additional_constraints=self.additional_constraints,
            timelimit=self.timelimit,
        )


def parse_xpansion_settings_local(data: Any) -> XpansionSettings:
    local_settings = XpansionSettingsLocal.model_validate(data)
    return local_settings.to_user_model()


def serialize_xpansion_settings_local(settings: XpansionSettingsType) -> dict[str, Any]:
    local_settings = XpansionSettingsLocal.from_user_model(settings)
    return local_settings.model_dump(mode="json", by_alias=True, exclude_none=True)
