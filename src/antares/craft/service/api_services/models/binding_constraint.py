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

from antares.craft.model.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
)
from antares.craft.model.commons import FILTER_VALUES, filtering_option
from antares.craft.service.api_services.models.base_model import APIBaseModel

BindingConstraintPropertiesType = BindingConstraintProperties | BindingConstraintPropertiesUpdate


class BindingConstraintPropertiesAPI(APIBaseModel):
    enabled: bool | None = None
    time_step: BindingConstraintFrequency | None = None
    operator: BindingConstraintOperator | None = None
    comments: str | None = None
    filter_year_by_year: filtering_option | None = None
    filter_synthesis: filtering_option | None = None
    group: str | None = None

    @staticmethod
    def from_user_model(user_class: BindingConstraintPropertiesType) -> "BindingConstraintPropertiesAPI":
        user_dict = asdict(user_class)
        return BindingConstraintPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> BindingConstraintProperties:
        content = self.model_dump(exclude_none=True)
        return BindingConstraintProperties(
            enabled=content.get("enabled", True),
            time_step=content.get("time_step", BindingConstraintFrequency.HOURLY),
            operator=content.get("operator", BindingConstraintOperator.LESS),
            comments=content.get("comments", ""),
            filter_year_by_year=content.get("filter_year_by_year", FILTER_VALUES),
            filter_synthesis=content.get("filter_synthesis", FILTER_VALUES),
            group=content.get("group", "default"),
        )
