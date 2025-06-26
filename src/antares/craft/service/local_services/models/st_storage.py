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

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.model.study import STUDY_VERSION_8_8
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.study.version import StudyVersion

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


def _sts_alias_generator(input: str) -> str:
    return input.replace("_", "")


class STStoragePropertiesLocal(LocalBaseModel, alias_generator=_sts_alias_generator):
    group: str = STStorageGroup.OTHER1.value
    injection_nominal_capacity: float = 0
    withdrawal_nominal_capacity: float = 0
    reservoir_capacity: float = 0
    efficiency: float = 1
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True
    # add new parameter 9.2
    efficiency_withdrawal: Optional[float] = None
    penalize_variation_injection: Optional[bool] = Field(None, alias="penalize-variation-injection")
    penalize_variation_withdrawal: Optional[bool] = Field(None, alias="penalize-variation-withdrawal")

    @field_validator("group")
    def validate_group(cls, v: str | STStorageGroup | None, info: ValidationInfo) -> str:
        study_version = info.context.get("study_version") if info.context is not None else None
        if study_version == STUDY_VERSION_8_8:
            if v is None or v == "":
                return STStorageGroup.OTHER1.value

            value = v.value if isinstance(v, STStorageGroup) else v
            valid_values = [e.value for e in STStorageGroup]

            if value not in valid_values:
                raise ValueError(f"Group for 8.8 has to be a valid value : {valid_values}")

            return value

        return str(v) if v is not None else ""

    @field_validator(
        "efficiency_withdrawal", "penalize_variation_injection", "penalize_variation_withdrawal", mode="before"
    )
    def check_version_support(cls, v: str | bool | float | None, info: ValidationInfo) -> Any:
        study_version = info.context.get("study_version") if info.context is not None else None
        if study_version == STUDY_VERSION_8_8:
            return None
        if v is None:
            if info.field_name == "efficiency_withdrawal":
                return 1.0
            return False
        return v

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType, study_version: StudyVersion) -> "STStoragePropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}

        if study_version == STUDY_VERSION_8_8:
            group = user_dict.get("group")
            if group is None or group == "":
                user_dict["group"] = STStorageGroup.OTHER1.value
                group = user_dict["group"]
            valid_values = [e.value for e in STStorageGroup]
            if group not in valid_values:
                raise ValueError("In 8.8, group must be a valid string value from STStorageGroup")

            fields_to_check = ["penalize_variation_injection", "penalize_variation_withdrawal", "efficiency_withdrawal"]

            violations = [field for field in fields_to_check if field in user_dict]
            if violations:
                raise ValueError(f"In version 8.8, the following values are not allowed: {', '.join(violations)}")
        else:
            if "efficiency_withdrawal" not in user_dict:
                user_dict["efficiency_withdrawal"] = 1.0
            if "penalize_variation_injection" not in user_dict:
                user_dict["penalize_variation_injection"] = False
            if "penalize_variation_withdrawal" not in user_dict:
                user_dict["penalize_variation_withdrawal"] = False

        return STStoragePropertiesLocal.model_validate(user_dict, context={"study_version": study_version})

    def to_user_model(self) -> STStorageProperties:
        # For version 9.2 and above, we need to set the default values for the new properties
        efficiency_withdrawal = self.efficiency_withdrawal
        penalize_variation_injection = self.penalize_variation_injection
        penalize_variation_withdrawal = self.penalize_variation_withdrawal

        # If we're in version 9.2 or above and the values are None, set the defaults
        if (
            efficiency_withdrawal is not None
            or penalize_variation_injection is not None
            or penalize_variation_withdrawal is not None
        ):
            if efficiency_withdrawal is None:
                efficiency_withdrawal = 1.0
            if penalize_variation_injection is None:
                penalize_variation_injection = False
            if penalize_variation_withdrawal is None:
                penalize_variation_withdrawal = False

        return STStorageProperties(
            enabled=self.enabled,
            group=self.group,
            injection_nominal_capacity=self.injection_nominal_capacity,
            withdrawal_nominal_capacity=self.withdrawal_nominal_capacity,
            reservoir_capacity=self.reservoir_capacity,
            efficiency=self.efficiency,
            initial_level=self.initial_level,
            initial_level_optim=self.initial_level_optim,
            efficiency_withdrawal=efficiency_withdrawal,
            penalize_variation_injection=penalize_variation_injection,
            penalize_variation_withdrawal=penalize_variation_withdrawal,
        )
