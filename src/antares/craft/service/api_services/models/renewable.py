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

from antares.craft.model.renewable import (
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    TimeSeriesInterpretation,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

RenewablePropertiesType = RenewableClusterProperties | RenewableClusterPropertiesUpdate


@all_optional_model
class RenewableClusterPropertiesAPI(APIBaseModel):
    group: RenewableClusterGroup
    ts_interpretation: TimeSeriesInterpretation
    enabled: bool
    unit_count: int
    nominal_capacity: float

    @staticmethod
    def from_user_model(user_class: RenewablePropertiesType) -> "RenewableClusterPropertiesAPI":
        user_dict = asdict(user_class)
        return RenewableClusterPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> RenewableClusterProperties:
        return RenewableClusterProperties(
            enabled=self.enabled,
            unit_count=self.unit_count,
            nominal_capacity=self.nominal_capacity,
            group=self.group,
            ts_interpretation=self.ts_interpretation,
        )
