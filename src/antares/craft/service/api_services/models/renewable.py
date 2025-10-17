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
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    TimeSeriesInterpretation,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null

RenewablePropertiesType = RenewableClusterProperties | RenewableClusterPropertiesUpdate


class RenewableClusterPropertiesAPI(APIBaseModel):
    group: str | None = None
    ts_interpretation: TimeSeriesInterpretation | None = None
    enabled: bool | None = None
    unit_count: int | None = None
    nominal_capacity: float | None = None

    @staticmethod
    def from_user_model(user_class: RenewablePropertiesType) -> "RenewableClusterPropertiesAPI":
        user_dict = asdict(user_class)
        return RenewableClusterPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> RenewableClusterProperties:
        return RenewableClusterProperties(
            enabled=check_field_is_not_null(self.enabled),
            unit_count=check_field_is_not_null(self.unit_count),
            nominal_capacity=check_field_is_not_null(self.nominal_capacity),
            group=check_field_is_not_null(self.group),
            ts_interpretation=check_field_is_not_null(self.ts_interpretation),
        )
