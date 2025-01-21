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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, MatrixDownloadError
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseHydroService


class HydroApiService(BaseHydroService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/maxpower_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "maxpower", e.message) from e

    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/reservoir_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "reservoir", e.message) from e

    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/inflowPattern_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "inflow_pattern", e.message) from e

    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/creditmodulations_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "credit_modulations", e.message) from e

    def get_water_values(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/waterValues_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "water_values", e.message) from e
