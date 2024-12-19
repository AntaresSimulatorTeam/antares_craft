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

from typing import Any, List

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.st_storage import STStorage, STStorageProperties
from antares.craft.service.base_services import BaseShortTermStorageService


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStorageProperties
    ) -> STStorageProperties:
        raise NotImplementedError

    def read_st_storages(self, area_id: str) -> List[STStorage]:
        raise NotImplementedError
