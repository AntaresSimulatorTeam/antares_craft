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
from typing import Any

from antares.craft.model.xpansion.sensitivity import XpansionSensitivity, XpansionSensitivityUpdate
from antares.craft.model.xpansion.settings import Master, Solver, UcType, XpansionSettings, XpansionSettingsUpdate
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

XpansionSettingsType = XpansionSettings | XpansionSettingsUpdate
XpansionSensitivityType = XpansionSensitivity | XpansionSensitivityUpdate


@all_optional_model
class XpansionSensitivityAPI(APIBaseModel):
    epsilon: float
    projection: list[str]
    capex: bool


@all_optional_model
class XpansionSettingsAPI(APIBaseModel):
    master: Master
    uc_type: UcType
    optimality_gap: float
    relative_gap: float
    relaxed_optimality_gap: float
    max_iteration: int
    solver: Solver
    log_level: int
    separation_parameter: float
    batch_size: int
    yearly_weights: str
    additional_constraints: str
    timelimit: int
    sensitivity_config: XpansionSensitivityAPI

    @staticmethod
    def from_user_model(
        settings_class: XpansionSettingsType | None, sensitivity_class: XpansionSensitivityType | None
    ) -> "XpansionSettingsAPI":
        settings_dict = asdict(settings_class) if settings_class else {}
        sensitivity_dict = {"sensitivity_config": asdict(sensitivity_class) if sensitivity_class else {}}
        settings_dict.update(sensitivity_dict)
        return XpansionSettingsAPI.model_validate(settings_dict)

    def to_sensitivity_model(self) -> XpansionSensitivity | None:
        if self.sensitivity_config is None:
            return None
        return XpansionSensitivity(
            epsilon=self.sensitivity_config.epsilon,
            projection=self.sensitivity_config.projection,
            capex=self.sensitivity_config.capex,
        )

    def to_settings_model(self) -> XpansionSettings:
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


def parse_xpansion_settings_api(data: dict[str, Any]) -> tuple[XpansionSettings, XpansionSensitivity | None]:
    api_model = XpansionSettingsAPI.model_validate(data)
    return api_model.to_settings_model(), api_model.to_sensitivity_model()


def serialize_xpansion_settings_api(
    settings_class: XpansionSettingsType | None, sensitivity_class: XpansionSensitivityType | None
) -> dict[str, Any]:
    api_model = XpansionSettingsAPI.from_user_model(settings_class, sensitivity_class)
    return api_model.model_dump(mode="json", by_alias=True, exclude_none=True)
