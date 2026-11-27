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

from pathlib import Path

from typing_extensions import override

from antares.craft import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, UserResourcesCreationError
from antares.craft.service.base_services import BaseUserResourcesService


class UserResourcesAPIService(BaseUserResourcesService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self._study_id = study_id
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())
        self._base_url = f"{self.config.get_host()}/api/v1"

    @property
    @override
    def study_id(self) -> str:
        return self._study_id

    @override
    def add_resource(self, relative_path: Path, content: bytes) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/user-resources?resource_type=file"
        try:
            self._wrapper.put(url, files={"file": (relative_path.as_posix(), content)})
        except APIError as e:
            raise UserResourcesCreationError(e.message) from e
