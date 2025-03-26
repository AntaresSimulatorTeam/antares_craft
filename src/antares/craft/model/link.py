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
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

import pandas as pd

from antares.craft.model.commons import FILTER_VALUES, FilterOption
from antares.craft.service.base_services import BaseLinkService
from antares.craft.tools.contents_tool import transform_name_to_id


class TransmissionCapacities(Enum):
    ENABLED = "enabled"
    DISABLED = "ignore"
    INFINITE = "infinite"


class AssetType(Enum):
    AC = "ac"
    DC = "dc"
    GAZ = "gaz"
    VIRTUAL = "virt"
    OTHER = "other"


class LinkStyle(Enum):
    DOT = "dot"
    PLAIN = "plain"
    DASH = "dash"
    DOT_DASH = "dotdash"


@dataclass
class LinkPropertiesUpdate:
    hurdles_cost: Optional[bool] = None
    loop_flow: Optional[bool] = None
    use_phase_shifter: Optional[bool] = None
    transmission_capacities: Optional[TransmissionCapacities] = None
    asset_type: Optional[AssetType] = None
    display_comments: Optional[bool] = None
    comments: Optional[str] = None
    filter_synthesis: Optional[set[FilterOption]] = None
    filter_year_by_year: Optional[set[FilterOption]] = None


@dataclass(frozen=True)
class LinkProperties:
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacities = TransmissionCapacities.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    comments: str = ""
    filter_synthesis: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    filter_year_by_year: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)


@dataclass(frozen=True)
class LinkUi:
    link_style: LinkStyle = LinkStyle.PLAIN
    link_width: float = 1
    colorr: int = 112
    colorg: int = 112
    colorb: int = 112


@dataclass
class LinkUiUpdate:
    link_style: Optional[LinkStyle] = None
    link_width: Optional[float] = None
    colorr: Optional[int] = None
    colorg: Optional[int] = None
    colorb: Optional[int] = None


class Link:
    def __init__(
        self,
        area_from: str,
        area_to: str,
        link_service: BaseLinkService,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
    ):
        self._area_from, self._area_to = sorted([area_from, area_to])
        self._link_service = link_service
        self._properties = properties or LinkProperties()
        self._ui = ui or LinkUi()

    @property
    def id(self) -> str:
        return self.area_from_id + " / " + self.area_to_id

    @property
    def area_from_id(self) -> str:
        return transform_name_to_id(self._area_from)

    @property
    def area_to_id(self) -> str:
        return transform_name_to_id(self._area_to)

    @property
    def properties(self) -> LinkProperties:
        return self._properties

    @property
    def ui(self) -> LinkUi:
        return self._ui

    def update_properties(self, properties: LinkPropertiesUpdate) -> LinkProperties:
        new_properties = self._link_service.update_links_properties({self.id: properties})
        self._properties = new_properties[self.id]
        return self._properties

    def update_ui(self, ui: LinkUiUpdate) -> LinkUi:
        new_ui = self._link_service.update_link_ui(self, ui)
        self._ui = new_ui
        return new_ui

    def set_parameters(self, series: pd.DataFrame) -> None:
        self._link_service.set_parameters(series, self.area_from_id, self.area_to_id)

    def set_capacity_direct(self, series: pd.DataFrame) -> None:
        self._link_service.set_capacity_direct(series, self.area_from_id, self.area_to_id)

    def set_capacity_indirect(self, series: pd.DataFrame) -> None:
        self._link_service.set_capacity_indirect(series, self.area_from_id, self.area_to_id)

    def get_capacity_direct(self) -> pd.DataFrame:
        return self._link_service.get_capacity_direct(self.area_from_id, self.area_to_id)

    def get_capacity_indirect(self) -> pd.DataFrame:
        return self._link_service.get_capacity_indirect(self.area_from_id, self.area_to_id)

    def get_parameters(self) -> pd.DataFrame:
        return self._link_service.get_parameters(self.area_from_id, self.area_to_id)
