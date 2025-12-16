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
from typing import Any

from pydantic import BaseModel, ConfigDict

from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.commons import FilterOption, filtering_option
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null

AreaPropertiesType = AreaProperties | AreaPropertiesUpdate


class AreaPropertiesAPIBase(APIBaseModel):
    energy_cost_unsupplied: float | None = None
    energy_cost_spilled: float | None = None
    non_dispatch_power: bool | None = None
    dispatch_hydro_power: bool | None = None
    other_dispatch_power: bool | None = None
    adequacy_patch_mode: AdequacyPatchMode | None = None
    spread_unsupplied_energy_cost: float | None = None
    spread_spilled_energy_cost: float | None = None

    def to_model(self, filter_synthesis: set[FilterOption], filter_by_year: set[FilterOption]) -> AreaProperties:
        return AreaProperties(
            energy_cost_unsupplied=check_field_is_not_null(self.energy_cost_unsupplied),
            energy_cost_spilled=check_field_is_not_null(self.energy_cost_spilled),
            non_dispatch_power=check_field_is_not_null(self.non_dispatch_power),
            dispatch_hydro_power=check_field_is_not_null(self.dispatch_hydro_power),
            other_dispatch_power=check_field_is_not_null(self.other_dispatch_power),
            filter_synthesis=filter_synthesis,
            filter_by_year=filter_by_year,
            adequacy_patch_mode=check_field_is_not_null(self.adequacy_patch_mode),
            spread_unsupplied_energy_cost=check_field_is_not_null(self.spread_unsupplied_energy_cost),
            spread_spilled_energy_cost=check_field_is_not_null(self.spread_spilled_energy_cost),
        )


class AreaPropertiesAPI(AreaPropertiesAPIBase):
    filter_synthesis: set[FilterOption] | None = None
    filter_by_year: set[FilterOption] | None = None

    @staticmethod
    def from_user_model(user_class: AreaPropertiesType) -> "AreaPropertiesAPI":
        user_dict = asdict(user_class)
        return AreaPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> AreaProperties:
        return super().to_model(
            filter_synthesis=check_field_is_not_null(self.filter_synthesis),
            filter_by_year=check_field_is_not_null(self.filter_by_year),
        )


class AreaPropertiesAPITableMode(AreaPropertiesAPIBase):
    filter_synthesis: filtering_option | None = None
    filter_by_year: filtering_option | None = None

    @staticmethod
    def from_user_model(user_class: AreaPropertiesType) -> "AreaPropertiesAPITableMode":
        user_dict = asdict(user_class)
        return AreaPropertiesAPITableMode.model_validate(user_dict)

    def to_user_model(self) -> AreaProperties:
        return super().to_model(
            filter_synthesis=check_field_is_not_null(self.filter_synthesis),
            filter_by_year=check_field_is_not_null(self.filter_by_year),
        )


AreaUiType = AreaUi | AreaUiUpdate


class Ui(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    x: int | None = None
    y: int | None = None
    color_r: int | None = None
    color_g: int | None = None
    color_b: int | None = None
    layers: str | None = None


class AreaUiAPI(APIBaseModel):
    ui: Ui | None = None
    layer_x: dict[int, int] | None = None
    layer_y: dict[int, int] | None = None
    layer_color: dict[int, str] | None = None

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
        assert self.ui is not None
        self.ui.x = self.ui.x or current_ui["x"]
        self.ui.y = self.ui.y or current_ui["y"]
        self.ui.color_r = self.ui.color_r or current_ui["color_r"]
        self.ui.color_g = self.ui.color_g or current_ui["color_g"]
        self.ui.color_b = self.ui.color_b or current_ui["color_b"]

    def to_api_dict(self) -> dict[str, Any]:
        assert self.ui is not None
        update_args = self.ui.model_dump(mode="json", by_alias=True, exclude={"layers"})
        update_args["color_rgb"] = [update_args.pop("color_r"), update_args.pop("color_g"), update_args.pop("color_b")]
        return update_args

    def to_user_model(self) -> AreaUi:
        assert self.ui is not None
        return AreaUi(
            x=check_field_is_not_null(self.ui.x),
            y=check_field_is_not_null(self.ui.y),
            color_rgb=[
                check_field_is_not_null(self.ui.color_r),
                check_field_is_not_null(self.ui.color_g),
                check_field_is_not_null(self.ui.color_b),
            ],
        )
