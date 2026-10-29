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

from urllib.parse import quote

from requests import RequestException
from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    DistrictCreationError,
    DistrictDeletionError,
    DistrictsRetrievalError,
)
from antares.craft.model.district import District, DistrictProperties
from antares.craft.service.api_services.models.district import DistrictAPI, parse_districts_api
from antares.craft.service.base_services import BaseDistrictService


class DistrictApiService(BaseDistrictService):
    def __init__(self, config: APIconf, study_id: str) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

    @override
    def read_districts(self, all_areas: list[str]) -> dict[str, District]:
        try:
            response = self._wrapper.get(f"{self._base_url}/studies/{self.study_id}/districts")
            return parse_districts_api(response.json(), self)
        except (APIError, RequestException, ValueError, KeyError) as e:
            raise DistrictsRetrievalError(self.study_id, str(e)) from e

    @override
    def create_districts(self, districts: dict[str, DistrictProperties]) -> list[District]:
        created: list[District] = []
        for name, properties in districts.items():
            try:
                body = DistrictAPI.from_user_model(name, properties).model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
                response = self._wrapper.post(f"{self._base_url}/studies/{self.study_id}/districts", json=body)
                created.extend(parse_districts_api([response.json()], self).values())
            except (APIError, RequestException, ValueError, KeyError) as e:
                raise DistrictCreationError(
                    name, str(e), created_districts=[district.name for district in created]
                ) from e
        return created

    @override
    def delete_district(self, district_id: str) -> None:
        try:
            self._wrapper.delete(f"{self._base_url}/studies/{self.study_id}/districts/{quote(district_id, safe='')}")
        except (APIError, RequestException) as e:
            raise DistrictDeletionError(district_id, str(e)) from e
