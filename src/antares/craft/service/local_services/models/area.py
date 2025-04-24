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
from dataclasses import asdict, field
from typing import Any

from pydantic import Field
from pydantic.alias_generators import to_camel

from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.commons import FILTER_VALUES, filtering_option
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab


class OptimizationPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    non_dispatchable_power: bool = True
    dispatchable_hydro_power: bool = True
    other_dispatchable_power: bool = True
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0


class FilteringPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    filter_synthesis: filtering_option = field(default_factory=lambda: FILTER_VALUES)
    filter_year_by_year: filtering_option = field(default_factory=lambda: FILTER_VALUES)


class AdequacyPatchPropertiesLocal(LocalBaseModel, alias_generator=to_kebab):
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE


class AreaPropertiesLocal(LocalBaseModel):
    nodal_optimization: OptimizationPropertiesLocal = Field(alias="nodal optimization")
    filtering: FilteringPropertiesLocal
    adequacy_patch: AdequacyPatchPropertiesLocal = Field(alias="adequacy-patch")
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0

    @staticmethod
    def _from_user_model_as_dict(params: dict[str, Any]) -> "AreaPropertiesLocal":
        args = {
            "adequacy_patch": {"adequacy_patch_mode": params["adequacy_patch_mode"]},
            "filtering": {
                "filter_synthesis": params["filter_synthesis"],
                "filter_year_by_year": params["filter_by_year"],
            },
            "nodal_optimization": {
                "non_dispatchable_power": params["non_dispatch_power"],
                "dispatchable_hydro_power": params["dispatch_hydro_power"],
                "other_dispatchable_power": params["other_dispatch_power"],
                "spread_unsupplied_energy_cost": params["spread_unsupplied_energy_cost"],
                "spread_spilled_energy_cost": params["spread_spilled_energy_cost"],
            },
            "energy_cost_unsupplied": params["energy_cost_unsupplied"],
            "energy_cost_spilled": params["energy_cost_spilled"],
        }
        return AreaPropertiesLocal.model_validate(args)

    @staticmethod
    def from_user_model(user_class: AreaProperties) -> "AreaPropertiesLocal":
        return AreaPropertiesLocal._from_user_model_as_dict(asdict(user_class))

    @staticmethod
    def build_for_update(update_class: AreaPropertiesUpdate, existing_class: AreaProperties) -> "AreaPropertiesLocal":
        params = asdict(existing_class)

        for key, value in asdict(update_class).items():
            if value is not None:
                params[key] = value

        return AreaPropertiesLocal._from_user_model_as_dict(params)

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


AreaUiType = AreaUi | AreaUiUpdate


class Ui(LocalBaseModel):
    x: int = 0
    y: int = 0
    color_r: int = 230
    color_g: int = 108
    color_b: int = 44
    layers: str = "0"


class AreaUiLocal(LocalBaseModel, alias_generator=to_camel):
    ui: Ui
    layer_x: dict[int, int] = {0: 0}
    layer_y: dict[int, int] = {0: 0}
    layer_color: dict[int, str] = {0: "0,0,0"}

    @staticmethod
    def from_user_model(user_class: AreaUi) -> "AreaUiLocal":
        x = user_class.x or 0
        y = user_class.y or 0
        args: dict[str, Any] = {
            "ui": {"x": x, "y": y},
            "layerX": {0: x},
            "layerY": {0: y},
        }
        if user_class.color_rgb:
            args["ui"].update(
                {
                    "color_r": user_class.color_rgb[0],
                    "color_g": user_class.color_rgb[1],
                    "color_b": user_class.color_rgb[2],
                }
            )
            args["layerColor"] = {0: ",".join(str(c) for c in user_class.color_rgb)}
        return AreaUiLocal.model_validate(args)

    @staticmethod
    def build_for_update(update_class: AreaUiUpdate, existing_class: AreaUi) -> "AreaUiLocal":
        x = update_class.x if update_class.x is not None else existing_class.x
        y = update_class.y if update_class.y is not None else existing_class.y
        args: dict[str, Any] = {
            "ui": {"x": x, "y": y},
            "layerX": {0: x},
            "layerY": {0: y},
        }
        class_to_consider: AreaUiType = update_class if update_class.color_rgb else existing_class
        assert class_to_consider.color_rgb is not None  # needed for mypy
        args["ui"].update(
            {
                "color_r": class_to_consider.color_rgb[0],
                "color_g": class_to_consider.color_rgb[1],
                "color_b": class_to_consider.color_rgb[2],
            }
        )
        args["layerColor"] = {0: ",".join(str(c) for c in class_to_consider.color_rgb)}

        return AreaUiLocal.model_validate(args)

    def to_user_model(self) -> AreaUi:
        return AreaUi(
            x=self.ui.x,
            y=self.ui.y,
            color_rgb=[self.ui.color_r, self.ui.color_g, self.ui.color_b],
        )
