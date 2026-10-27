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

from typing import Literal

from pydantic import Field

from antares.craft.model.district import District
from antares.craft.service.local_services.models.base_model import LocalBaseModel


class DistrictLocal(LocalBaseModel, extra="allow"):
    """District definition in sets.ini, including its area selection rules.

    Additional fields, such as the output filters introduced in 10.2, are
    accepted even though they are not exposed by the user model.
    """

    name: str = Field(default="", alias="caption")
    output: bool = True
    comments: str = ""
    apply_filter: Literal["add-all", "remove-all"] = Field(default="remove-all", alias="apply-filter")
    add_areas: list[str] = Field(default_factory=list, alias="+")
    subtract_areas: list[str] = Field(default_factory=list, alias="-")

    def to_user_model(self, all_areas: list[str]) -> District:
        # Match the effective areas returned by Antares Web's District.to_dto().
        if self.apply_filter == "add-all":
            areas = set(all_areas).difference(self.subtract_areas)
        else:
            areas = set(self.add_areas)
        return District(name=self.name, output=self.output, comments=self.comments, areas=sorted(areas))
