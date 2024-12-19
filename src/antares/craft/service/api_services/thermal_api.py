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

from pathlib import PurePosixPath
from typing import List

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, ThermalMatrixDownloadError, ThermalPropertiesUpdateError
from antares.craft.model.thermal import ThermalCluster, ThermalClusterMatrixName, ThermalClusterProperties
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseThermalService


class ThermalApiService(BaseThermalService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterProperties
    ) -> ThermalClusterProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{thermal_cluster.area_id}/clusters/thermal/{thermal_cluster.id}"
        try:
            body = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not body:
                return thermal_cluster.properties

            response = self._wrapper.patch(url, json=body)
            json_response = response.json()
            del json_response["id"]
            del json_response["name"]
            new_properties = ThermalClusterProperties.model_validate(json_response)

        except APIError as e:
            raise ThermalPropertiesUpdateError(thermal_cluster.id, thermal_cluster.area_id, e.message) from e

        return new_properties

    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        try:
            keyword = "series" if "SERIES" in ts_name.name else "prepro"
            path = (
                PurePosixPath("input")
                / "thermal"
                / keyword
                / f"{thermal_cluster.area_id}"
                / f"{thermal_cluster.name.lower()}"
                / ts_name.value
            )
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise ThermalMatrixDownloadError(
                thermal_cluster.area_id, thermal_cluster.name, ts_name.value, e.message
            ) from e

    def read_thermal_clusters(
        self,
        area_id: str,
    ) -> List[ThermalCluster]:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/thermal"
        json_thermal = self._wrapper.get(url).json()

        thermals = []

        for thermal in json_thermal:
            thermal_id = thermal.pop("id")
            thermal_name = thermal.pop("name")

            thermal_props = ThermalClusterProperties(**thermal)
            thermal_cluster = ThermalCluster(self, thermal_id, thermal_name, thermal_props)
            thermals.append(thermal_cluster)

        thermals.sort(key=lambda thermal: thermal.id)

        return thermals
