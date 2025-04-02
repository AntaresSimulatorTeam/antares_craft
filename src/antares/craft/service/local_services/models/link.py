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
from typing import Optional

from antares.craft.model.commons import FILTER_VALUES, filtering_option
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

LinkPropertiesType = LinkProperties | LinkPropertiesUpdate
LinkUiType = LinkUi | LinkUiUpdate


class LinkPropertiesAndUiLocal(LocalBaseModel, alias_generator=to_kebab):
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacities = TransmissionCapacities.ENABLED
    asset_type: AssetType = AssetType.AC
    link_style: LinkStyle = LinkStyle.PLAIN
    link_width: float = 1
    colorr: int = 112
    colorg: int = 112
    colorb: int = 112
    display_comments: bool = True
    filter_synthesis: filtering_option = field(default_factory=lambda: FILTER_VALUES)
    filter_year_by_year: filtering_option = field(default_factory=lambda: FILTER_VALUES)
    comments: str = ""

    @staticmethod
    def from_user_model(
        ui_class: Optional[LinkUiType] = None, properties_class: Optional[LinkPropertiesType] = None
    ) -> "LinkPropertiesAndUiLocal":
        ui_dict = {k: v for k, v in asdict(ui_class).items() if v is not None} if ui_class else {}
        props_dict = {k: v for k, v in asdict(properties_class).items() if v is not None} if properties_class else {}
        return LinkPropertiesAndUiLocal.model_validate({**ui_dict, **props_dict})

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
