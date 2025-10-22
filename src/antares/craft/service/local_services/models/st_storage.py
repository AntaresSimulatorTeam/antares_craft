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
import re

from dataclasses import asdict
from typing import Annotated, Any, Optional, TypeAlias

from pydantic import BeforeValidator, Field, PlainSerializer

from antares.craft.model.commons import STUDY_VERSION_9_2, STUDY_VERSION_9_3
from antares.craft.model.st_storage import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    Occurrence,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintUpdate,
    STStorageGroup,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
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
    initial_level: float = Field(default=0.5, ge=0, le=1)
    initial_level_optim: bool = False
    enabled: bool = True
    # Introduced in v9.2
    efficiency_withdrawal: Optional[float] = Field(None, ge=0)
    penalize_variation_injection: Optional[bool] = Field(None, alias="penalize-variation-injection")
    penalize_variation_withdrawal: Optional[bool] = Field(None, alias="penalize-variation-withdrawal")
    # Introduced in v9.3
    allow_overflow: Optional[bool] = Field(None, alias="allow-overflow")

    @staticmethod
    def get_9_2_fields_and_default_value() -> dict[str, Any]:
        return {
            "efficiency_withdrawal": 1,
            "penalize_variation_injection": False,
            "penalize_variation_withdrawal": False,
        }

    @staticmethod
    def get_9_3_fields_and_default_value() -> dict[str, Any]:
        return {"allow_overflow": False}

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
            allow_overflow=self.allow_overflow,
        )


def validate_st_storage_against_version(properties: STStoragePropertiesLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_9_2:
        valid_values = [e.value for e in STStorageGroup] + [None]
        if properties.group not in valid_values:
            raise ValueError(f"Group for 8.8 has to be a valid value : {valid_values}")

        for field in STStoragePropertiesLocal.get_9_2_fields_and_default_value():
            check_min_version(properties, field, version)

        if properties.efficiency > 1:
            raise ValueError(f"Prior to v9.2, efficiency must be lower than 1 and was {properties.efficiency}")

    else:
        efficiency_withdrawal = 1 if properties.efficiency_withdrawal is None else properties.efficiency_withdrawal
        if properties.efficiency > efficiency_withdrawal:
            raise ValueError(
                f"efficiency must be lower than efficiency_withdrawal. Currently: {properties.efficiency} > {efficiency_withdrawal}"
            )

        if version < STUDY_VERSION_9_3:
            for field in STStoragePropertiesLocal.get_9_3_fields_and_default_value():
                check_min_version(properties, field, version)


def initialize_with_version(properties: STStoragePropertiesLocal, version: StudyVersion) -> STStoragePropertiesLocal:
    if version >= STUDY_VERSION_9_2:
        for field, value in STStoragePropertiesLocal.get_9_2_fields_and_default_value().items():
            initialize_field_default(properties, field, value)
    if version >= STUDY_VERSION_9_3:
        for field, value in STStoragePropertiesLocal.get_9_3_fields_and_default_value().items():
            initialize_field_default(properties, field, value)
    return properties


def parse_st_storage_local(study_version: StudyVersion, data: Any) -> STStorageProperties:
    local_properties = STStoragePropertiesLocal.model_validate(data)
    validate_st_storage_against_version(local_properties, study_version)
    initialize_with_version(local_properties, study_version)
    return local_properties.to_user_model()


def serialize_st_storage_local(study_version: StudyVersion, storage: STStoragePropertiesType) -> dict[str, Any]:
    local_properties = STStoragePropertiesLocal.from_user_model(storage)
    validate_st_storage_against_version(local_properties, study_version)
    return local_properties.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)


##########################
# Additional constraints part
##########################

HoursType: TypeAlias = list[list[int]]


def _check_hours_compliance(value: int) -> int:
    if not isinstance(value, int) or not (1 <= value <= 168):
        raise ValueError(f"Hours must be integers between 1 and 168, got {value}")
    return value


def _hours_parser(value: str | HoursType) -> HoursType:
    def _string_to_list(s: str) -> HoursType:
        to_return = []
        numbers_as_list = re.findall(r"\[(.*?)\]", s)
        if numbers_as_list == [""]:
            # Happens if the given string is `[]`
            return [[]]
        for numbers in numbers_as_list:
            to_return.append([int(v) for v in numbers.split(",")])
        return to_return

    if isinstance(value, str):
        value = _string_to_list(value)
    for item in value:
        for subitem in item:
            _check_hours_compliance(subitem)
    return value


def _hours_serializer(value: HoursType) -> str:
    return ", ".join(str(v) for v in value)


Hours: TypeAlias = Annotated[HoursType, BeforeValidator(_hours_parser), PlainSerializer(_hours_serializer)]


class STStorageAdditionalConstraintLocal(LocalBaseModel):
    name: str
    variable: AdditionalConstraintVariable = AdditionalConstraintVariable.NETTING
    operator: AdditionalConstraintOperator = AdditionalConstraintOperator.LESS
    hours: Hours
    enabled: bool = True

    @staticmethod
    def from_user_model(user_class: STStorageAdditionalConstraint) -> "STStorageAdditionalConstraintLocal":
        user_dict = asdict(user_class)
        del user_dict["id"]
        del user_dict["occurrences"]
        user_dict["hours"] = [[]]
        if user_class.occurrences:
            user_dict["hours"] = []
            for occ in user_class.occurrences:
                user_dict["hours"].append(occ.hours)
        return STStorageAdditionalConstraintLocal.model_validate(user_dict)

    def to_user_model(self) -> STStorageAdditionalConstraint:
        occurrences = [Occurrence(hours=hour) for hour in self.hours if hour]
        return STStorageAdditionalConstraint(
            name=self.name,
            variable=self.variable,
            operator=self.operator,
            occurrences=occurrences,
            enabled=self.enabled,
        )


def parse_st_storage_constraint_local(data: Any) -> STStorageAdditionalConstraint:
    return STStorageAdditionalConstraintLocal.model_validate(data).to_user_model()


def serialize_st_storage_constraint_local(constraint: STStorageAdditionalConstraint) -> dict[str, Any]:
    return STStorageAdditionalConstraintLocal.from_user_model(constraint).model_dump(mode="json", exclude_none=True)


def update_st_storage_constraint_local(
    constraint: STStorageAdditionalConstraint, data: STStorageAdditionalConstraintUpdate
) -> STStorageAdditionalConstraint:
    return STStorageAdditionalConstraint(
        name=constraint.name,
        variable=data.variable or constraint.variable,
        operator=data.operator or constraint.operator,
        occurrences=data.occurrences or constraint.occurrences,
        enabled=data.enabled or constraint.enabled,
    )
