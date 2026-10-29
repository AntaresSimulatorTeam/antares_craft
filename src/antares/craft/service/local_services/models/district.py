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
from typing import Literal

from pydantic import Field, field_validator

from antares.craft.model.commons import STUDY_VERSION_10_2
from antares.craft.model.district import DistrictProperties
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.utils import FILTER_VALUES, filtering_option
from antares.study.version import StudyVersion


class DistrictLocal(LocalBaseModel, extra="allow"):
    """District definition in sets.ini."""

    name: str = Field(default="", alias="caption")
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
        return set() if value == "" else value

    def initialize_with_version(self, study_version: StudyVersion) -> None:
        for field in ("filter_synthesis", "filter_year_by_year"):
            if study_version < STUDY_VERSION_10_2:
                check_min_version(self, field, study_version)
            else:
                initialize_field_default(self, field, FILTER_VALUES.copy())

    @staticmethod
    def from_user_model(name: str, properties: DistrictProperties, study_version: StudyVersion) -> "DistrictLocal":
        values = {"name": name, **asdict(properties)}
        values["comments"] = properties.comments.strip()
        values["add_areas"] = sorted(set(values.pop("areas")))
        model = DistrictLocal.model_validate(values)
        model.initialize_with_version(study_version)
        return model

    def to_properties_user_model(self, all_areas: list[str], study_version: StudyVersion) -> DistrictProperties:
        """Resolve areas using the same filter semantics as AntaresWeb."""
        areas = (
            set(all_areas).difference(self.subtract_areas) if self.apply_filter == "add-all" else set(self.add_areas)
        )
        self.initialize_with_version(study_version)
        return DistrictProperties(
            output=self.output,
            comments=self.comments,
            areas=sorted(areas),
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )
