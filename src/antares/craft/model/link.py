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
from typing import Mapping, Optional, Set

import pandas as pd

from antares.craft.model.commons import FilterOption, default_filtering
from antares.craft.service.base_services import BaseLinkService
from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import transform_name_to_id
from pydantic import BaseModel


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
    filter_synthesis: Optional[Set[FilterOption]] = None
    filter_year_by_year: Optional[Set[FilterOption]] = None


@dataclass
class LinkProperties:
    hurdles_cost: bool = False
    loop_flow: bool = False
    use_phase_shifter: bool = False
    transmission_capacities: TransmissionCapacities = TransmissionCapacities.ENABLED
    asset_type: AssetType = AssetType.AC
    display_comments: bool = True
    comments: str = ""
    filter_synthesis: Set[FilterOption] = field(default_factory=default_filtering)
    filter_year_by_year: Set[FilterOption] = field(default_factory=default_filtering)


class DefaultLinkUi(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_kebab):
    """
    DTO for updating link UI
    """

    link_style: LinkStyle = LinkStyle.PLAIN
    link_width: float = 1
    colorr: int = 112
    colorg: int = 112
    colorb: int = 112


@all_optional_model
class LinkUi(DefaultLinkUi):
    pass


class LinkUiLocal(DefaultLinkUi):
    @property
    def ini_fields(self) -> Mapping[str, str]:
        # todo: can be replaced with alias i believe
        return {
            "link-style": f"{self.link_style.value}",
            "link-width": f"{self.link_width}",
            "colorr": f"{self.colorr}",
            "colorg": f"{self.colorg}",
            "colorb": f"{self.colorb}",
        }

    def yield_link_ui(self) -> LinkUi:
        excludes = {"ini_fields"}
        return LinkUi.model_validate(self.model_dump(mode="json", exclude=excludes))


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

    def update_properties(self, properties: LinkProperties) -> LinkProperties:
        new_properties = self._link_service.update_link_properties(self, properties)
        self._properties = new_properties
        return new_properties

    def update_ui(self, ui: LinkUi) -> LinkUi:
        new_ui = self._link_service.update_link_ui(self, ui)
        self._ui = new_ui
        return new_ui

    def create_parameters(self, series: pd.DataFrame) -> None:
        self._link_service.create_parameters(series, self.area_from_id, self.area_to_id)

    def create_capacity_direct(self, series: pd.DataFrame) -> None:
        self._link_service.create_capacity_direct(series, self.area_from_id, self.area_to_id)

    def create_capacity_indirect(self, series: pd.DataFrame) -> None:
        self._link_service.create_capacity_indirect(series, self.area_from_id, self.area_to_id)

    def get_capacity_direct(self) -> pd.DataFrame:
        return self._link_service.get_capacity_direct(self.area_from_id, self.area_to_id)

    def get_capacity_indirect(self) -> pd.DataFrame:
        return self._link_service.get_capacity_indirect(self.area_from_id, self.area_to_id)

    def get_parameters(self) -> pd.DataFrame:
        return self._link_service.get_parameters(self.area_from_id, self.area_to_id)
