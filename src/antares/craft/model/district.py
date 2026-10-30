# Copyright (c) 2024-2026, RTE (https://www.rte-france.com)
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
from typing import TYPE_CHECKING

from antares.craft.model.commons import FilterOption
from antares.craft.tools.contents_tool import transform_name_to_id

if TYPE_CHECKING:
    from antares.craft.service.base_services import BaseDistrictService


@dataclass(frozen=True)
class DistrictProperties:
    """Represents a spatial aggregate of study areas.

    Attributes:
        output: Whether to generate simulation outputs for the district.
        comments: Description of the district.
        areas: Identifiers of the areas belonging to the district.
        filter_synthesis: Output frequencies for synthesis results (since v10.2).
        filter_year_by_year: Output frequencies for yearly results (since v10.2).
            Both filters default to all frequencies in v10.2 and later, and are
            unavailable (None) in earlier versions. An empty set disables all frequencies.
    """

    output: bool = True
    comments: str = ""
    areas: list[str] = field(default_factory=list)
    filter_synthesis: set[FilterOption] | None = None
    filter_year_by_year: set[FilterOption] | None = None

    def __post_init__(self) -> None:
        if "\n" in self.comments or "\r" in self.comments:
            raise ValueError("Multiline district comments are not supported")


class District:
    """A spatial aggregate of study areas."""

    def __init__(
        self,
        name: str,
        district_service: "BaseDistrictService",
        properties: DistrictProperties | None = None,
        *,
        district_id: str | None = None,
    ) -> None:
        self._name = name
        self._id = district_id if district_id is not None else transform_name_to_id(name)
        self._district_service = district_service
        self._properties = properties or DistrictProperties()

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def properties(self) -> DistrictProperties:
        return self._properties
