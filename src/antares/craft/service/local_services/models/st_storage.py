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
from typing import Any, Union

from pydantic import Field, field_validator
from pydantic_core.core_schema import ValidationInfo

from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.study.version import StudyVersion

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


def _sts_alias_generator(input: str) -> str:
    return input.replace("_", "")


class STStoragePropertiesLocal(LocalBaseModel, alias_generator=_sts_alias_generator):
    group: STStorageGroup | str = Field(default="")
    injection_nominal_capacity: float = 0
    withdrawal_nominal_capacity: float = 0
    reservoir_capacity: float = 0
    efficiency: float = 1
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True
    # add new parameter 9.2
    efficiency_withdrawal: float = 1

    penalize_variation_injection: bool = Field(False, alias="penalize-variation-injection")
    penalize_variation_withdrawal: bool = Field(False, alias="penalize-variation-withdrawal")

    @field_validator("group")
    def validate_group(cls, v: str | STStorageGroup | None, info: ValidationInfo) -> str | STStorageGroup:
        study_version = getattr(info.context, "get", lambda x: None)("study_version")
        if study_version == StudyVersion.parse("8.8"):
            if v is None or v == "":
                return STStorageGroup.OTHER1
            if isinstance(v, str):
                try:
                    return STStorageGroup(v)
                except ValueError:
                    raise ValueError(f"Group for 8.8 has to be a valid value : {[e.value for e in STStorageGroup]}")
            return v
        return v if v is not None else ""

    @field_validator("efficiency_withdrawal", "penalize_variation_injection", "penalize_variation_withdrawal")
    def check_version_support(cls, v: Union[str, STStorageGroup], info: ValidationInfo) -> Any:
        study_version = getattr(info.context, "get", lambda x: None)("study_version")
        if study_version == StudyVersion.parse("8.8"):
            return None
        return v

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType, study_version: StudyVersion) -> "STStoragePropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}

        if study_version == StudyVersion.parse("8.8"):
            if "group" not in user_dict:
                user_dict["group"] = STStorageGroup.OTHER1
            elif isinstance(user_dict["group"], str):
                try:
                    user_dict["group"] = STStorageGroup(user_dict["group"])
                except ValueError:
                    raise ValueError(f"Group for 8.8 has to be a valid value : {[e.value for e in STStorageGroup]}")
        else:
            user_dict["group"] = user_dict.get("group", "")

        return STStoragePropertiesLocal.model_validate(user_dict, context={"study_version": study_version})

    def to_user_model(self) -> STStorageProperties:
        group_value = self.group
        if hasattr(self, "_context") and self._context.get("study_version") == StudyVersion.parse("8.8"):
            if isinstance(self.group, str):
                group_value = STStorageGroup(self.group)

        return STStorageProperties(
            enabled=self.enabled,
            group=group_value,
            injection_nominal_capacity=self.injection_nominal_capacity,
            withdrawal_nominal_capacity=self.withdrawal_nominal_capacity,
            reservoir_capacity=self.reservoir_capacity,
            efficiency=self.efficiency,
            initial_level=self.initial_level,
            initial_level_optim=self.initial_level_optim,
            efficiency_withdrawal=self.efficiency_withdrawal,
            penalize_variation_injection=self.penalize_variation_injection,
            penalize_variation_withdrawal=self.penalize_variation_withdrawal,
        )
