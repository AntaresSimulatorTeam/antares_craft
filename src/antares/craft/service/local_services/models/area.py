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
from dataclasses import field
from typing import Union

from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate
from antares.craft.model.commons import FILTER_VALUES, comma_separated_enum_set
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab
from pydantic import Field

AreaPropertiesType = Union[AreaProperties, AreaPropertiesUpdate]


class OptimizationPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    non_dispatchable_power: bool = True
    dispatchable_hydro_power: bool = True
    other_dispatchable_power: bool = True
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0


class FilteringPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    filter_synthesis: comma_separated_enum_set = field(default_factory=lambda: FILTER_VALUES)
    filter_year_by_year: comma_separated_enum_set = field(default_factory=lambda: FILTER_VALUES)


class AdequacyPatchPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE


class AreaPropertiesLocal(LocalBaseModel):
    nodal_optimization: OptimizationPropertiesLocal = Field(alias="nodal optimization")
    filtering: FilteringPropertiesLocal
    adequacy_patch: AdequacyPatchPropertiesLocal = Field(alias="adequacy-patch")
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0

    @staticmethod
    def from_user_model(user_class: AreaPropertiesType) -> "AreaPropertiesLocal":
        args = {
            "adequacy_patch": {"adequacy_patch_mode": user_class.adequacy_patch_mode},
            "filtering": {
                "filter_synthesis": user_class.filter_synthesis,
                "filter_year_by_year": user_class.filter_by_year,
            },
            "nodal_optimization": {
                "non_dispatchable_power": user_class.non_dispatch_power,
                "dispatchable_hydro_power": user_class.dispatch_hydro_power,
                "other_dispatchable_power": user_class.other_dispatch_power,
                "spread_unsupplied_energy_cost": user_class.spread_unsupplied_energy_cost,
                "spread_spilled_energy_cost": user_class.spread_spilled_energy_cost,
            },
            "energy_cost_unsupplied": user_class.energy_cost_unsupplied,
            "energy_cost_spilled": user_class.energy_cost_spilled,
        }

        return AreaPropertiesLocal.model_validate(args)

    def to_user_model(self) -> AreaProperties:
        return AreaProperties(
            energy_cost_unsupplied=self.energy_cost_unsupplied,
            energy_cost_spilled=self.energy_cost_spilled,
            non_dispatch_power=self.nodal_optimization.non_dispatchable_power,
            dispatch_hydro_power=self.nodal_optimization.dispatchable_hydro_power,
            other_dispatch_power=self.nodal_optimization.other_dispatchable_power,
            filter_synthesis=self.filtering.filter_synthesis,
            filter_by_year=self.filtering.filter_year_by_year,
            adequacy_patch_mode=self.adequacy_patch.adequacy_patch_mode,
            spread_unsupplied_energy_cost=self.nodal_optimization.spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=self.nodal_optimization.spread_spilled_energy_cost,
        )

    def to_adequacy_ini(self) -> dict[str, dict[str, str]]:
        return self.model_dump(mode="json", include={"adequacy_patch"}, by_alias=True)

    def to_optimization_ini(self) -> dict[str, dict[str, str]]:
        return self.model_dump(mode="json", include={"nodal_optimization", "filtering"}, by_alias=True)
