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

from dataclasses import asdict
from typing import Any, Literal

from pydantic import Field, field_validator

from antares.craft.model.commons import STUDY_VERSION_10_2
from antares.craft.model.district import DistrictProperties
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.utils import FILTER_VALUES, filtering_option
from antares.study.version import StudyVersion


class DistrictPropertiesLocal(LocalBaseModel):
    """District properties in sets.ini."""

    output: bool = True
    comments: str = ""
    apply_filter: Literal["add-all", "remove-all"] = Field(default="remove-all", alias="apply-filter")
    add_areas: list[str] = Field(default_factory=list, alias="+")
    subtract_areas: list[str] = Field(default_factory=list, alias="-")
    filter_synthesis: filtering_option | None = Field(default=None, alias="filter-synthesis")
    filter_year_by_year: filtering_option | None = Field(default=None, alias="filter-year-by-year")

    @field_validator("filter_synthesis", "filter_year_by_year", mode="before")
    @classmethod
    def preserve_empty_filters(cls, value: object) -> object:
        # Preserve an empty filter: LocalBaseModel would replace "" with None and restore all frequencies.
        return set() if value == "" else value

    @staticmethod
    def get_10_2_fields_and_default_value() -> dict[str, Any]:
        return {"filter_synthesis": FILTER_VALUES.copy(), "filter_year_by_year": FILTER_VALUES.copy()}

    @staticmethod
    def from_user_model(properties: DistrictProperties) -> "DistrictPropertiesLocal":
        values = asdict(properties)
        values["comments"] = properties.comments.strip()
        values["add_areas"] = sorted(set(values.pop("areas")))
        return DistrictPropertiesLocal.model_validate(values)

    def to_user_model(self, all_areas: list[str]) -> DistrictProperties:
        """Resolve areas using the same filter semantics as AntaresWeb."""
        areas = (
            set(all_areas).difference(self.subtract_areas) if self.apply_filter == "add-all" else set(self.add_areas)
        )
        return DistrictProperties(
            output=self.output,
            comments=self.comments,
            areas=sorted(areas),
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )


def validate_district_against_version(properties: DistrictPropertiesLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_10_2:
        for field in DistrictPropertiesLocal.get_10_2_fields_and_default_value():
            check_min_version(properties, field, version)


def initialize_with_version(properties: DistrictPropertiesLocal, version: StudyVersion) -> DistrictPropertiesLocal:
    if version >= STUDY_VERSION_10_2:
        for field, value in DistrictPropertiesLocal.get_10_2_fields_and_default_value().items():
            initialize_field_default(properties, field, value)
    return properties


def parse_district_local(version: StudyVersion, data: Any, all_areas: list[str]) -> DistrictProperties:
    properties = DistrictPropertiesLocal.model_validate(data)
    validate_district_against_version(properties, version)
    initialize_with_version(properties, version)
    return properties.to_user_model(all_areas)


def serialize_district_local(version: StudyVersion, properties: DistrictProperties) -> dict[str, Any]:
    local_properties = DistrictPropertiesLocal.from_user_model(properties)
    validate_district_against_version(local_properties, version)
    initialize_with_version(local_properties, version)
    return local_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
