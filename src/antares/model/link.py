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

from enum import Enum
from typing import Optional, Set, Any, Mapping

from pydantic import BaseModel, computed_field

from antares.model.area import Area
from antares.model.commons import FilterOption, sort_filter_values


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


def link_aliasing(string: str) -> str:
    return string.replace("_", "-")


class LinkProperties(
    BaseModel, extra="forbid", populate_by_name=True, alias_generator=link_aliasing
):
    """
    DTO for updating link properties
    """

    hurdles_cost: Optional[bool] = None
    loop_flow: Optional[bool] = None
    use_phase_shifter: Optional[bool] = None
    transmission_capacities: Optional[TransmissionCapacities] = None
    asset_type: Optional[AssetType] = None
    display_comments: Optional[bool] = None
    filter_synthesis: Optional[Set[FilterOption]] = None
    filter_year_by_year: Optional[Set[FilterOption]] = None


# TODO update to use check_if_none
class LinkPropertiesLocal(BaseModel):
    def __init__(
        self,
        link_properties: LinkProperties = LinkProperties(),
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        self._hurdles_cost = link_properties.hurdles_cost or False
        self._loop_flow = link_properties.loop_flow or False
        self._use_phase_shifter = link_properties.use_phase_shifter or False
        self._transmission_capacities = (
            link_properties.transmission_capacities
            if link_properties.transmission_capacities
            else TransmissionCapacities.ENABLED
        )
        self._asset_type = (
            link_properties.asset_type if link_properties.asset_type else AssetType.AC
        )
        self._display_comments = link_properties.display_comments or True
        self._filter_synthesis = link_properties.filter_synthesis or {
            FilterOption.HOURLY,
            FilterOption.DAILY,
            FilterOption.WEEKLY,
            FilterOption.MONTHLY,
            FilterOption.ANNUAL,
        }
        self._filter_year_by_year = link_properties.filter_year_by_year or {
            FilterOption.HOURLY,
            FilterOption.DAILY,
            FilterOption.WEEKLY,
            FilterOption.MONTHLY,
            FilterOption.ANNUAL,
        }

    @computed_field  # type: ignore[misc]
    @property
    def ini_fields(self) -> Mapping[str, str]:
        return {
            "hurdles-cost": f"{self._hurdles_cost}".lower(),
            "loop-flow": f"{self._loop_flow}".lower(),
            "use-phase-shifter": f"{self._use_phase_shifter}".lower(),
            "transmission-capacities": f"{self._transmission_capacities.value}",
            "asset-type": f"{self._asset_type.value}",
            "display-comments": f"{self._display_comments}".lower(),
            "filter-synthesis": ", ".join(
                filter_value
                for filter_value in sort_filter_values(self._filter_synthesis)
            ),
            "filter-year-by-year": ", ".join(
                filter_value
                for filter_value in sort_filter_values(self._filter_year_by_year)
            ),
        }

    def yield_link_properties(self) -> LinkProperties:
        return LinkProperties(
            hurdles_cost=self._hurdles_cost,
            loop_flow=self._loop_flow,
            use_phase_shifter=self._use_phase_shifter,
            transmission_capacities=self._transmission_capacities,
            asset_type=self._asset_type,
            display_comments=self._display_comments,
            filter_synthesis=self._filter_synthesis,
            filter_year_by_year=self._filter_year_by_year,
        )


class LinkUi(
    BaseModel, extra="forbid", populate_by_name=True, alias_generator=link_aliasing
):
    """
    DTO for updating link UI
    """

    link_style: Optional[LinkStyle] = None
    link_width: Optional[float] = None
    colorr: Optional[int] = None
    colorg: Optional[int] = None
    colorb: Optional[int] = None


class LinkUiLocal(BaseModel):
    def __init__(
        self,
        link_ui: LinkUi = LinkUi(),
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        self._link_style = link_ui.link_style if link_ui.link_style else LinkStyle.PLAIN
        self._link_width = link_ui.link_width if link_ui.link_width is not None else 1
        self._colorr = link_ui.colorr if link_ui.colorr is not None else 112
        self._colorg = link_ui.colorg if link_ui.colorg is not None else 112
        self._colorb = link_ui.colorb if link_ui.colorb is not None else 112

    @computed_field  # type: ignore[misc]
    @property
    def ini_fields(self) -> Mapping[str, str]:
        return {
            "link-style": f"{self._link_style.value}",
            "link-width": f"{self._link_width}",
            "colorr": f"{self._colorr}",
            "colorg": f"{self._colorg}",
            "colorb": f"{self._colorb}",
        }

    def yield_link_ui(self) -> LinkUi:
        return LinkUi(
            link_style=self._link_style,
            link_width=self._link_width,
            colorr=self._colorr,
            colorg=self._colorg,
            colorb=self._colorb,
        )


class Link:
    def __init__(  # type: ignore # TODO: Find a way to avoid circular imports
        self,
        area_from: Area,
        area_to: Area,
        link_service,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
    ):
        self._area_from = area_from
        self._area_to = area_to
        self._link_service = link_service
        self._properties = properties or LinkProperties()
        self._ui = ui or LinkUi()

    @property
    def name(self) -> str:
        return self._area_from.id + " / " + self._area_to.id

    @property
    def area_from(self) -> Area:
        return self._area_from

    @property
    def area_to(self) -> Area:
        return self._area_to

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

    # todo: Add matrices
