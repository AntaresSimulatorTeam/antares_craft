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
from typing import Annotated, Any, Optional, TypeAlias

from pydantic import Field

from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.model.study import STUDY_VERSION_9_2
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.study.version import StudyVersion

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


def _sts_alias_generator(input: str) -> str:
    return input.replace("_", "")


Capacity: TypeAlias = Annotated[float, Field(default=0, ge=0)]


class STStoragePropertiesLocal(LocalBaseModel, alias_generator=_sts_alias_generator):
    group: str = STStorageGroup.OTHER1.value
    injection_nominal_capacity: Capacity
    withdrawal_nominal_capacity: Capacity
    reservoir_capacity: Capacity
    efficiency: float = Field(1, ge=0)
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True
    # add new parameter 9.2
    efficiency_withdrawal: Optional[float] = Field(None, ge=0)
    penalize_variation_injection: Optional[bool] = Field(None, alias="penalize-variation-injection")
    penalize_variation_withdrawal: Optional[bool] = Field(None, alias="penalize-variation-withdrawal")

    @staticmethod
    def get_9_2_fields_and_default_value() -> dict[str, Any]:
        return {
            "efficiency_withdrawal": 1,
            "penalize_variation_injection": False,
            "penalize_variation_withdrawal": False,
        }

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return STStoragePropertiesLocal.model_validate(user_dict)

    def to_user_model(self) -> STStorageProperties:
        return STStorageProperties(
            enabled=self.enabled,
            group=self.group,
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


def validate_st_storage_against_version(properties: STStoragePropertiesLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_9_2:
        valid_values = [e.value for e in STStorageGroup] + [None]
        if properties.group not in valid_values:
            raise ValueError(f"Group for 8.8 has to be a valid value : {valid_values}")

        for field in STStoragePropertiesLocal.get_9_2_fields_and_default_value():
            check_min_version(properties, field, version)


def initialize_with_version(properties: STStoragePropertiesLocal, version: StudyVersion) -> STStoragePropertiesLocal:
    if version >= STUDY_VERSION_9_2:
        for field, value in STStoragePropertiesLocal.get_9_2_fields_and_default_value().items():
            initialize_field_default(properties, field, value)
    return properties


def validate_attributes_coherence(properties: STStoragePropertiesLocal, version: StudyVersion) -> None:
    if version >= STUDY_VERSION_9_2:
        assert isinstance(properties.efficiency, (float, int))
        assert isinstance(properties.efficiency_withdrawal, (float, int))
        if properties.efficiency > properties.efficiency_withdrawal:
            raise ValueError("efficiency_withdrawal must be greater than efficiency")


def parse_st_storage_local(study_version: StudyVersion, data: Any) -> STStorageProperties:
    local_properties = STStoragePropertiesLocal.model_validate(data)
    validate_st_storage_against_version(local_properties, study_version)
    initialize_with_version(local_properties, study_version)
    validate_attributes_coherence(local_properties, study_version)
    return local_properties.to_user_model()


def serialize_st_storage_local(study_version: StudyVersion, storage: STStoragePropertiesType) -> dict[str, Any]:
    local_properties = STStoragePropertiesLocal.from_user_model(storage)
    validate_st_storage_against_version(local_properties, study_version)
    return local_properties.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)
