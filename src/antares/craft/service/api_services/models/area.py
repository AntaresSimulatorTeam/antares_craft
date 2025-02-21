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
from typing import Any, Union

from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.commons import FilterOption
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, ConfigDict

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


AreaUiType = Union[AreaUi, AreaUiUpdate]


@all_optional_model
class Ui(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    x: int
    y: int
    color_r: int
    color_g: int
    color_b: int
    layers: str


@all_optional_model
class AreaUiAPI(APIBaseModel):
    ui: Ui
    layer_x: dict[int, int]
    layer_y: dict[int, int]
    layer_color: dict[int, str]

    @staticmethod
    def from_user_model(user_class: AreaUiType) -> "AreaUiAPI":
        args = {"ui": {"x": user_class.x, "y": user_class.y}}
        if user_class.color_rgb:
            args["ui"].update(
                {
                    "color_r": user_class.color_rgb[0],
                    "color_g": user_class.color_rgb[1],
                    "color_b": user_class.color_rgb[2],
                }
            )
        return AreaUiAPI.model_validate(args)

    def update_from_get(self, api_response: dict[str, Any]) -> None:
        current_ui = api_response["ui"]
        self.ui.x = current_ui["x"]
        self.ui.y = current_ui["y"]
        self.ui.color_r = current_ui["color_r"]
        self.ui.color_g = current_ui["color_g"]
        self.ui.color_b = current_ui["color_b"]

    def to_api_dict(self) -> dict[str, Any]:
        update_args = self.ui.model_dump(mode="json", by_alias=True, exclude={"layers"})
        update_args["color_rgb"] = [update_args.pop("color_r"), update_args.pop("color_g"), update_args.pop("color_b")]
        return update_args

    def to_user_model(self) -> AreaUi:
        return AreaUi(
            x=self.ui.x,
            y=self.ui.y,
            color_rgb=[self.ui.color_r, self.ui.color_g, self.ui.color_b],
        )
