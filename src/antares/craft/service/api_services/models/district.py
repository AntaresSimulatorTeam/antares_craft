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
from typing import Any

from antares.craft.model.district import District, DistrictProperties
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.base_services import BaseDistrictService
from antares.craft.tools.utils import filtering_option


class DistrictAPI(APIBaseModel):
    name: str
    output: bool
    comments: str
    areas: list[str]
    filter_synthesis: filtering_option | None = None
    filter_year_by_year: filtering_option | None = None

    @staticmethod
    def from_user_model(name: str, properties: DistrictProperties) -> "DistrictAPI":
        return DistrictAPI.model_validate({"name": name, **asdict(properties)})

    def to_properties_user_model(self) -> DistrictProperties:
        return DistrictProperties(
            output=self.output,
            comments=self.comments,
            areas=sorted(set(self.areas)),
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )


def parse_districts_api(data: list[dict[str, Any]], service: BaseDistrictService) -> dict[str, District]:
    return {
        item["id"]: District(
            item["name"], service, DistrictAPI.model_validate(item).to_properties_user_model(), district_id=item["id"]
        )
        for item in data
    }
