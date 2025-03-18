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
from antares.craft.model.commons import filtering_option
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

BindingConstraintPropertiesType = BindingConstraintProperties | BindingConstraintPropertiesUpdate


@all_optional_model
class BindingConstraintPropertiesAPI(APIBaseModel):
    enabled: bool
    time_step: BindingConstraintFrequency
    operator: BindingConstraintOperator
    comments: str
    filter_year_by_year: filtering_option
    filter_synthesis: filtering_option
    group: str

    @staticmethod
    def from_user_model(user_class: BindingConstraintPropertiesType) -> "BindingConstraintPropertiesAPI":
        user_dict = asdict(user_class)
        return BindingConstraintPropertiesAPI.model_validate(user_dict)

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
