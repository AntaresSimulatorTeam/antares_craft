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

from pydantic import Field

from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

STStoragePropertiesType = STStorageProperties | STStoragePropertiesUpdate


@all_optional_model
class STStoragePropertiesAPI(APIBaseModel):
    group: STStorageGroup
    injection_nominal_capacity: float
    withdrawal_nominal_capacity: float
    reservoir_capacity: float
    efficiency: float
    initial_level: float
    initial_level_optim: bool
    enabled: bool
    # add new parameter 9.2 but not study_version validation in API
    efficiency_withdrawal: float = 1
    penalize_variation_injection: bool = Field(False, serialization_alias="penalize-variation-injection")
    penalize_variation_withdrawal: bool = Field(False, serialization_alias="penalize-variation-withdrawal")

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesAPI":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
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
