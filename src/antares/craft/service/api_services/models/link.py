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
from typing import Optional

from antares.craft.model.commons import filtering_option
from antares.craft.model.link import (
    AssetType,
    LinkProperties,
    LinkPropertiesUpdate,
    LinkStyle,
    LinkUi,
    LinkUiUpdate,
    TransmissionCapacities,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.all_optional_meta import all_optional_model

LinkPropertiesType = LinkProperties | LinkPropertiesUpdate
LinkUiType = LinkUi | LinkUiUpdate


@all_optional_model
class LinkPropertiesAndUiAPI(APIBaseModel):
    hurdles_cost: bool
    loop_flow: bool
    use_phase_shifter: bool
    transmission_capacities: TransmissionCapacities
    asset_type: AssetType
    display_comments: bool
    comments: str
    filter_synthesis: filtering_option
    filter_year_by_year: filtering_option
    link_style: LinkStyle
    link_width: float
    colorr: int
    colorg: int
    colorb: int

    @staticmethod
    def from_user_model(
        ui_class: Optional[LinkUiType] = None, properties_class: Optional[LinkPropertiesType] = None
    ) -> "LinkPropertiesAndUiAPI":
        ui_dict = asdict(ui_class) if ui_class else {}
        properties_dict = asdict(properties_class) if properties_class else {}
        return LinkPropertiesAndUiAPI.model_validate({**ui_dict, **properties_dict})

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
