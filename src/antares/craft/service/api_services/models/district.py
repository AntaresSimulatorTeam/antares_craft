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

from antares.craft.model.district import DistrictProperties, DistrictPropertiesUpdate
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null
from antares.craft.tools.utils import filtering_option

DistrictPropertiesType = DistrictProperties | DistrictPropertiesUpdate


class DistrictPropertiesAPI(APIBaseModel):
    output: bool | None = None
    comments: str | None = None
    areas: list[str] | None = None
    apply_filter: Literal["add-all", "remove-all"] | None = None
    filter_synthesis: filtering_option | None = None
    filter_year_by_year: filtering_option | None = None

    @staticmethod
    def from_user_model(user_class: DistrictPropertiesType) -> "DistrictPropertiesAPI":
        user_dict = asdict(user_class)
        if user_class.areas is not None:
            user_dict["apply_filter"] = "remove-all"
        return DistrictPropertiesAPI.model_validate(user_dict)

    def to_user_model(self) -> DistrictProperties:
        return DistrictProperties(
            output=check_field_is_not_null(self.output),
            comments=check_field_is_not_null(self.comments),
            areas=sorted(set(check_field_is_not_null(self.areas))),
            filter_synthesis=self.filter_synthesis,
            filter_year_by_year=self.filter_year_by_year,
        )


def parse_district_api(data: Any) -> DistrictProperties:
    return DistrictPropertiesAPI.model_validate(data).to_user_model()


def serialize_district_api(properties: DistrictPropertiesType) -> dict[str, Any]:
    return DistrictPropertiesAPI.from_user_model(properties).model_dump(
        mode="json", by_alias=True, exclude_none=True, exclude_unset=True
    )
