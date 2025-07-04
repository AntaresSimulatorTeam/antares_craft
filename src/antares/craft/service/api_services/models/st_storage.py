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

from antares.craft.model.st_storage import STStorageProperties, STStoragePropertiesUpdate
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


@all_optional_model
class STStoragePropertiesAPI(APIBaseModel):
    group: str
    injection_nominal_capacity: float
    withdrawal_nominal_capacity: float
    reservoir_capacity: float
    efficiency: float
    initial_level: float
    initial_level_optim: bool
    enabled: bool
    # add new parameter 9.2
    efficiency_withdrawal: float
    penalize_variation_injection: bool
    penalize_variation_withdrawal: bool

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesAPI":
        user_dict = asdict(user_class)
        return STStoragePropertiesAPI.model_validate(user_dict)

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


def parse_st_storage_api(data: Any) -> STStorageProperties:
    return STStoragePropertiesAPI.model_validate(data).to_user_model()


def serialize_st_storage_api(storage: STStoragePropertiesType) -> dict[str, Any]:
    return STStoragePropertiesAPI.from_user_model(storage).model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude_unset=True
    )
