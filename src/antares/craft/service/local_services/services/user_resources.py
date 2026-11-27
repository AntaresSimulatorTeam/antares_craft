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

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.service.base_services import BaseUserResourcesService


class UserResourcesLocalService(BaseUserResourcesService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self._study_name = study_name
        self._user_path = self.config.study_path / "user"

    @property
    @override
    def study_id(self) -> str:
        return self._study_name

    @override
    def add_resource(self, relative_path: Path, content: bytes) -> None:
        # todo: ensures the path isn't traversal.
        pass
