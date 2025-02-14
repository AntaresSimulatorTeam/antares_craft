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
from typing import Any, Optional, Union

from antares.craft.model.commons import FilterOption, default_filtering
from antares.craft.model.link import (
    AssetType,
    LinkProperties,
    LinkPropertiesUpdate,
    LinkStyle,
    LinkUi,
    LinkUiUpdate,
    TransmissionCapacities,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab
from pydantic import field_validator

LinkPropertiesType = Union[LinkProperties, LinkPropertiesUpdate]
LinkUiType = Union[LinkUi, LinkUiUpdate]


class LinkPropertiesAndUiLocal(LocalBaseModel, alias_generator=to_kebab):
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacities = TransmissionCapacities.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    comments: str = ""
    filter_synthesis: set[FilterOption] = field(default_factory=default_filtering)
    filter_year_by_year: set[FilterOption] = field(default_factory=default_filtering)
    link_style: LinkStyle
    link_width: float
    colorr: int
    colorg: int
    colorb: int

    @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
    def validate_filtering(cls, v: Any) -> set[str]:
        if v is None:
            return set()
        if isinstance(v, (list, set)):
            return set(v)
        if isinstance(v, str):
            if v[0] == "[":
                v = v[1:-1]
            return set(v.replace(" ", "").split(","))
        raise ValueError(f"Value {v} not supported for filtering")

    @staticmethod
    def from_user_model(
        ui_class: Optional[LinkUiType] = None, properties_class: Optional[LinkPropertiesType] = None
    ) -> "LinkPropertiesAndUiLocal":
        ui_dict = asdict(ui_class) if ui_class else {}
        properties_dict = asdict(properties_class) if properties_class else {}
        return LinkPropertiesAndUiLocal.model_validate({**ui_dict, **properties_dict})

    def to_ui_user_model(self) -> LinkUi:
        return LinkUi(
            link_style=self.link_style,
            link_width=self.link_width,
            colorr=self.colorr,
            colorg=self.colorg,
            colorb=self.colorb,
        )

    def to_properties_user_model(self) -> LinkProperties:
        return LinkProperties(
            hurdles_cost=self.hurdles_cost,
            loop_flow=self.loop_flow,
            use_phase_shifter=self.use_phase_shifter,
            transmission_capacities=self.transmission_capacities,
            asset_type=self.asset_type,
            display_comments=self.display_comments,
            comments=self.comments,
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )
