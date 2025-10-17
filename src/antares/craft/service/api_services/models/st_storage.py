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

from antares.craft.model.st_storage import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    Occurrence,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintUpdate,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


class STStoragePropertiesAPI(APIBaseModel):
    group: str | None = None
    injection_nominal_capacity: float | None = None
    withdrawal_nominal_capacity: float | None = None
    reservoir_capacity: float | None = None
    efficiency: float | None = None
    initial_level: float | None = None
    initial_level_optim: bool | None = None
    enabled: bool | None = None
    # Introduced in v9.2
    efficiency_withdrawal: float | None = None
    penalize_variation_injection: bool | None = None
    penalize_variation_withdrawal: bool | None = None
    # Introduced in v9.3
    allow_overflow: bool | None = None

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesAPI":
        user_dict = asdict(user_class)
        return STStoragePropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> STStorageProperties:
        return STStorageProperties(
            enabled=check_field_is_not_null(self.enabled),
            group=check_field_is_not_null(self.group),
            injection_nominal_capacity=check_field_is_not_null(self.injection_nominal_capacity),
            withdrawal_nominal_capacity=check_field_is_not_null(self.withdrawal_nominal_capacity),
            reservoir_capacity=check_field_is_not_null(self.reservoir_capacity),
            efficiency=check_field_is_not_null(self.efficiency),
            initial_level=check_field_is_not_null(self.initial_level),
            initial_level_optim=check_field_is_not_null(self.initial_level_optim),
            efficiency_withdrawal=self.efficiency_withdrawal,
            penalize_variation_injection=self.penalize_variation_injection,
            penalize_variation_withdrawal=self.penalize_variation_withdrawal,
            allow_overflow=self.allow_overflow,
        )


def parse_st_storage_api(data: Any) -> STStorageProperties:
    return STStoragePropertiesAPI.model_validate(data).to_user_model()


def serialize_st_storage_api(storage: STStoragePropertiesType) -> dict[str, Any]:
    return STStoragePropertiesAPI.from_user_model(storage).model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude_unset=True
    )


##########################
# Additional constraints part
##########################

STStorageConstraintType = STStorageAdditionalConstraint | STStorageAdditionalConstraintUpdate


class OccurrenceAPI(APIBaseModel):
    hours: list[int]


class STStorageAdditionalConstraintAPI(APIBaseModel):
    id: str | None = None
    name: str | None = None
    variable: AdditionalConstraintVariable | None = None
    operator: AdditionalConstraintOperator | None = None
    occurrences: list[OccurrenceAPI] | None = None
    enabled: bool | None = None

    @staticmethod
    def from_user_model(user_class: STStorageConstraintType) -> "STStorageAdditionalConstraintAPI":
        user_dict = asdict(user_class)
        return STStorageAdditionalConstraintAPI.model_validate(user_dict)

    def to_user_model(self) -> STStorageAdditionalConstraint:
        assert self.occurrences is not None
        occurrences = [Occurrence(hours=occ.model_dump()["hours"]) for occ in self.occurrences]
        return STStorageAdditionalConstraint(
            name=check_field_is_not_null(self.name),
            variable=check_field_is_not_null(self.variable),
            operator=check_field_is_not_null(self.operator),
            occurrences=check_field_is_not_null(occurrences),
            enabled=check_field_is_not_null(self.enabled),
        )


def parse_st_storage_constraint_api(data: Any) -> STStorageAdditionalConstraint:
    return STStorageAdditionalConstraintAPI.model_validate(data).to_user_model()


def serialize_st_storage_constraint_api(constraint: STStorageConstraintType) -> dict[str, Any]:
    return STStorageAdditionalConstraintAPI.from_user_model(constraint).model_dump(
        mode="json", exclude_none=True, exclude={"id"}
    )
