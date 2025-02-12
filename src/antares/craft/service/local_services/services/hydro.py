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

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.hydro import HydroPropertiesUpdate
from antares.craft.service.base_services import BaseHydroService
from typing_extensions import override


class HydroLocalService(BaseHydroService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self.study_name = study_name

    @override
    def update_properties(self, area_id: str, properties: HydroPropertiesUpdate) -> None:
        raise NotImplementedError

    @override
    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    @override
    def get_water_values(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()
