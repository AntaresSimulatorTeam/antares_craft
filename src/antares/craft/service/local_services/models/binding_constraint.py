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

from antares.craft.model.binding_constraint import (
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from pydantic import Field

BindingConstraintPropertiesType = Union[BindingConstraintProperties, BindingConstraintPropertiesUpdate]


class BindingConstraintPropertiesLocal(LocalBaseModel):
    enabled: bool = True
    time_step: BindingConstraintFrequency = Field(BindingConstraintFrequency.HOURLY, alias="type")
    operator: BindingConstraintOperator = BindingConstraintOperator.LESS
    comments: str = ""
    filter_year_by_year: str = Field("hourly", alias="filter-year-by-year")
    filter_synthesis: str = Field("hourly", alias="filter-synthesis")
    group: str = "default"

    @staticmethod
    def from_user_model(user_class: BindingConstraintPropertiesType) -> "BindingConstraintPropertiesLocal":
        user_dict = asdict(user_class)
        return BindingConstraintPropertiesLocal.model_validate(user_dict)

    def to_user_model(self) -> BindingConstraintProperties:
        return BindingConstraintProperties(
            enabled=self.enabled,
            time_step=self.time_step,
            operator=self.operator,
            comments=self.comments,
            filter_year_by_year=self.filter_year_by_year,
            filter_synthesis=self.filter_synthesis,
            group=self.group,
        )
