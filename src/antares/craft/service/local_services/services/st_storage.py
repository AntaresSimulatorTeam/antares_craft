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

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.st_storage import (
    STStorage,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.base_services import BaseShortTermStorageService
from typing_extensions import override


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStoragePropertiesUpdate
    ) -> STStorageProperties:
        raise NotImplementedError

    @override
    def read_st_storages(self, area_id: str) -> List[STStorage]:
        raise NotImplementedError

    @override
    def update_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        raise NotImplementedError

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        raise NotImplementedError
