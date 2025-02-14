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

from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate
from antares.craft.model.commons import FilterOption
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

AreaPropertiesType = Union[AreaProperties, AreaPropertiesUpdate]


@all_optional_model
class AreaPropertiesAPI(APIBaseModel):
    energy_cost_unsupplied: float
    energy_cost_spilled: float
    non_dispatch_power: bool
    dispatch_hydro_power: bool
    other_dispatch_power: bool
    filter_synthesis: set[FilterOption]
    filter_by_year: set[FilterOption]
    adequacy_patch_mode: AdequacyPatchMode
    spread_unsupplied_energy_cost: float
    spread_spilled_energy_cost: float

    @staticmethod
    def from_user_model(user_class: AreaPropertiesType) -> "AreaPropertiesAPI":
        user_dict = asdict(user_class)
        return AreaPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> AreaProperties:
        return AreaProperties(
            energy_cost_unsupplied=self.energy_cost_spilled,
            energy_cost_spilled=self.energy_cost_spilled,
            non_dispatch_power=self.non_dispatch_power,
            dispatch_hydro_power=self.dispatch_hydro_power,
            other_dispatch_power=self.other_dispatch_power,
            filter_synthesis=self.filter_synthesis,
            filter_by_year=self.filter_by_year,
            adequacy_patch_mode=self.adequacy_patch_mode,
            spread_unsupplied_energy_cost=self.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=self.spread_spilled_energy_cost,
        )
