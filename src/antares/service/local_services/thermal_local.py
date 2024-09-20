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

from typing import Any

import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.model.thermal import ThermalCluster, ThermalClusterMatrixName, ThermalClusterProperties
from antares.service.base_services import BaseThermalService


class ThermalLocalService(BaseThermalService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterProperties
    ) -> ThermalClusterProperties:
        raise NotImplementedError

    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        raise NotImplementedError
