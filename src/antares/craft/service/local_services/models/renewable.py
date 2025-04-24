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

from antares.craft.model.renewable import (
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    TimeSeriesInterpretation,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel

RenewablePropertiesType = RenewableClusterProperties | RenewableClusterPropertiesUpdate


class RenewableClusterPropertiesLocal(LocalBaseModel):
    enabled: bool = True
    unit_count: int = Field(default=1, alias="unitcount")
    nominal_capacity: float = Field(default=0, alias="nominalcapacity")
    group: RenewableClusterGroup = RenewableClusterGroup.OTHER1
    ts_interpretation: TimeSeriesInterpretation = Field(
        default=TimeSeriesInterpretation.POWER_GENERATION, alias="ts-interpretation"
    )

    @staticmethod
    def from_user_model(user_class: RenewablePropertiesType) -> "RenewableClusterPropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return RenewableClusterPropertiesLocal.model_validate(user_dict)

    def to_user_model(self) -> RenewableClusterProperties:
        return RenewableClusterProperties(
            enabled=self.enabled,
            unit_count=self.unit_count,
            nominal_capacity=self.nominal_capacity,
            group=self.group,
            ts_interpretation=self.ts_interpretation,
        )
