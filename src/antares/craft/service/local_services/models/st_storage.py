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
from typing import Union

from antares.craft.model.st_storage import STStorageGroup, STStorageProperties, STStoragePropertiesUpdate
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

STStoragePropertiesType = Union[STStorageProperties, STStoragePropertiesUpdate]


def _sts_alias_generator(input: str) -> str:
    return input.replace("_", "")


@all_optional_model
class STStoragePropertiesLocal(LocalBaseModel, alias_generator=_sts_alias_generator):
    group: STStorageGroup = STStorageGroup.OTHER1
    injection_nominal_capacity: float = 0
    withdrawal_nominal_capacity: float = 0
    reservoir_capacity: float = 0
    efficiency: float = 1
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True

    @staticmethod
    def from_user_model(user_class: STStoragePropertiesType) -> "STStoragePropertiesLocal":
        user_dict = asdict(user_class)
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
        )
