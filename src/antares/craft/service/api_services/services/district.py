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
)
from antares.craft.model.district import District, DistrictProperties
from antares.craft.service.api_services.models.district import parse_district_api, serialize_district_api
from antares.craft.service.base_services import BaseDistrictService


class DistrictApiService(BaseDistrictService):
    def __init__(self, config: APIconf, study_id: str) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

    @override
    def create_districts(self, districts: dict[str, DistrictProperties]) -> list[District]:
        created: list[District] = []
        for name, properties in districts.items():
            try:
                body = {"name": name, **serialize_district_api(properties)}
                response = self._wrapper.post(f"{self._base_url}/studies/{self.study_id}/districts", json=body)
                item = response.json()
                created.append(District(item["name"], self, parse_district_api(item), district_id=item["id"]))
            except (APIError, RequestException, ValueError, KeyError) as e:
                raise DistrictCreationError(name, str(e)) from e
        return created

    @override
    def delete_district(self, district_id: str) -> None:
        try:
            self._wrapper.delete(f"{self._base_url}/studies/{self.study_id}/districts/{quote(district_id, safe='')}")
        except (APIError, RequestException) as e:
            raise DistrictDeletionError(district_id, str(e)) from e
