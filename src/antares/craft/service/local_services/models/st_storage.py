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

from antares.craft.exceptions.exceptions import InvalidFieldForVersionError
from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.model.study import STUDY_VERSION_9_2
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

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return STStoragePropertiesLocal.model_validate(user_dict)

    def to_user_model(self, study_version: StudyVersion) -> STStorageProperties:
        # fmt: off
        efficiency_withdrawal = self.efficiency_withdrawal or (1 if study_version >= STUDY_VERSION_9_2 else None)
        penalize_variation_injection = self.penalize_variation_injection or (False if study_version >= STUDY_VERSION_9_2 else None)
        penalize_variation_withdrawal = self.penalize_variation_withdrawal or (False if study_version >= STUDY_VERSION_9_2 else None)
        # fmt: on
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


def _check_min_version(data: Any, field: str, version: StudyVersion) -> None:
    if getattr(data, field) is not None:
        raise InvalidFieldForVersionError(f"Field {field} is not a valid field for study version {version}")


def validate_st_storage_against_version(
    version: StudyVersion,
    storage_data: STStoragePropertiesType,
) -> None:
    """
    Validates input short-term storage data against the provided study versions

    Will raise an InvalidFieldForVersionError if a field is not valid for the given study version.
    """
    if version < STUDY_VERSION_9_2:
        for field in ["efficiency_withdrawal", "penalize_variation_injection", "penalize_variation_withdrawal"]:
            _check_min_version(storage_data, field, version)


def parse_st_storage_local(study_version: StudyVersion, data: Any) -> STStorageProperties:
    storage = STStoragePropertiesLocal.model_validate(data).to_user_model(study_version)
    validate_st_storage_against_version(study_version, storage)
    return storage


def serialize_st_storage_local(study_version: StudyVersion, storage: STStoragePropertiesType) -> dict[str, Any]:
    validate_st_storage_against_version(study_version, storage)
    return STStoragePropertiesLocal.from_user_model(storage).model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude_unset=True
    )
