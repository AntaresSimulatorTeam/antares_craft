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
from antares.craft.service.utils import check_field_is_not_null

LinkPropertiesType = LinkProperties | LinkPropertiesUpdate
LinkUiType = LinkUi | LinkUiUpdate


class LinkPropertiesAndUiAPI(APIBaseModel):
    hurdles_cost: bool | None = None
    loop_flow: bool | None = None
    use_phase_shifter: bool | None = None
    transmission_capacities: TransmissionCapacities | None = None
    asset_type: AssetType | None = None
    display_comments: bool | None = None
    comments: str | None = None
    filter_synthesis: filtering_option | None = None
    filter_year_by_year: filtering_option | None = None
    link_style: LinkStyle | None = None
    link_width: float | None = None
    colorr: int | None = None
    colorg: int | None = None
    colorb: int | None = None

    @staticmethod
    def from_user_model(
        ui_class: Optional[LinkUiType] = None, properties_class: Optional[LinkPropertiesType] = None
    ) -> "LinkPropertiesAndUiAPI":
        ui_dict = asdict(ui_class) if ui_class else {}
        properties_dict = asdict(properties_class) if properties_class else {}
        return LinkPropertiesAndUiAPI.model_validate({**ui_dict, **properties_dict})

    def to_ui_user_model(self) -> LinkUi:
        return LinkUi(
            link_style=check_field_is_not_null(self.link_style),
            link_width=check_field_is_not_null(self.link_width),
            colorr=check_field_is_not_null(self.colorr),
            colorg=check_field_is_not_null(self.colorg),
            colorb=check_field_is_not_null(self.colorb),
        )

    def to_properties_user_model(self) -> LinkProperties:
        return LinkProperties(
            hurdles_cost=check_field_is_not_null(self.hurdles_cost),
            loop_flow=check_field_is_not_null(self.loop_flow),
            use_phase_shifter=check_field_is_not_null(self.use_phase_shifter),
            transmission_capacities=check_field_is_not_null(self.transmission_capacities),
            asset_type=check_field_is_not_null(self.asset_type),
            display_comments=check_field_is_not_null(self.display_comments),
            comments=check_field_is_not_null(self.comments),
            filter_synthesis=check_field_is_not_null(self.filter_synthesis),
            filter_year_by_year=check_field_is_not_null(self.filter_year_by_year),
        )
