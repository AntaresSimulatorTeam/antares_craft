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

from pydantic import Field

from antares.craft.model.commons import STUDY_VERSION_10_2
from antares.craft.model.district import District
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.utils import FILTER_VALUES, join_with_comma
from antares.study.version import StudyVersion


class DistrictLocal(LocalBaseModel, extra="allow"):
    """District definition in sets.ini."""

    name: str = Field(default="", alias="caption")
    output: bool = True
    comments: str = ""
    apply_filter: Literal["add-all", "remove-all"] = Field(default="remove-all", alias="apply-filter")
    add_areas: list[str] = Field(default_factory=list, alias="+")
    subtract_areas: list[str] = Field(default_factory=list, alias="-")

    @staticmethod
    def from_user_model(district: District, study_version: StudyVersion) -> "DistrictLocal":
        values = asdict(district)
        values["add_areas"] = sorted(set(values.pop("areas")))
        if study_version >= STUDY_VERSION_10_2:
            filters = join_with_comma(FILTER_VALUES)
            values.update({"filter-synthesis": filters, "filter-year-by-year": filters})
        return DistrictLocal.model_validate(values)

    def to_user_model(self, all_areas: list[str]) -> District:
        if self.apply_filter == "add-all":
            areas = set(all_areas).difference(self.subtract_areas)
        else:
            areas = set(self.add_areas)
        return District(name=self.name, output=self.output, comments=self.comments, areas=sorted(areas))
