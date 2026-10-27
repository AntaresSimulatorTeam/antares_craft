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

from dataclasses import asdict
from typing import Any

from antares.craft.model.district import District
from antares.craft.service.api_services.models.base_model import APIBaseModel


class DistrictAPI(APIBaseModel):
    name: str
    output: bool
    comments: str
    areas: list[str]

    @staticmethod
    def from_user_model(district: District) -> "DistrictAPI":
        return DistrictAPI.model_validate(asdict(district))

    def to_user_model(self) -> District:
        return District(name=self.name, output=self.output, comments=self.comments, areas=sorted(set(self.areas)))


def parse_districts_api(data: list[dict[str, Any]]) -> dict[str, District]:
    return {item["id"]: DistrictAPI.model_validate(item).to_user_model() for item in data}
