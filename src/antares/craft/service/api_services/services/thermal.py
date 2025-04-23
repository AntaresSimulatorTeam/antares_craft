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

import pandas as pd

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    ClustersPropertiesUpdateError,
    ThermalMatrixDownloadError,
    ThermalMatrixUpdateError,
)
from antares.craft.model.thermal import (
    ThermalCluster,
    ThermalClusterMatrixName,
    ThermalClusterProperties,
    ThermalClusterPropertiesUpdate,
)
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import BaseThermalService


class ThermalApiService(BaseThermalService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def set_thermal_matrix(
        self, thermal_cluster: ThermalCluster, matrix: pd.DataFrame, ts_name: ThermalClusterMatrixName
    ) -> None:
        keyword = "series" if "SERIES" in ts_name.name else "prepro"
        path = (
            PurePosixPath("input")
            / "thermal"
            / keyword
            / f"{thermal_cluster.area_id}"
            / f"{thermal_cluster.id}"
            / ts_name.value
        )
        try:
            update_series(self._base_url, self.study_id, self._wrapper, matrix, path.as_posix())
        except APIError as e:
            raise ThermalMatrixUpdateError(
                thermal_cluster.area_id, thermal_cluster.name, ts_name.value, e.message
            ) from e

    @override
    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        try:
            keyword = "series" if "SERIES" in ts_name.name else "prepro"
            path = (
                PurePosixPath("input")
                / "thermal"
                / keyword
                / f"{thermal_cluster.area_id}"
                / f"{thermal_cluster.id.lower()}"
                / ts_name.value
            )
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise ThermalMatrixDownloadError(
                thermal_cluster.area_id, thermal_cluster.name, ts_name.value, e.message
            ) from e

    @override
    def read_thermal_clusters(self) -> dict[str, dict[str, ThermalCluster]]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/thermals"
        json_thermal = self._wrapper.get(url).json()

        thermals: dict[str, dict[str, ThermalCluster]] = {}

        for key, thermal in json_thermal.items():
            area_id, thermal_id = key.split(" / ")
            api_props = ThermalClusterPropertiesAPI.model_validate(thermal)
            thermal_props = api_props.to_user_model()
            thermal_cluster = ThermalCluster(self, area_id, thermal_id, thermal_props)

            thermals.setdefault(area_id, {})[thermal_cluster.id] = thermal_cluster

        return thermals

    @override
    def update_thermal_clusters_properties(
        self, new_properties: dict[ThermalCluster, ThermalClusterPropertiesUpdate]
    ) -> dict[ThermalCluster, ThermalClusterProperties]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/thermals"

        cluster_dict = {}  # Used to fill the method's response

        body = {}
        for cluster, props in new_properties.items():
            api_properties = ThermalClusterPropertiesAPI.from_user_model(props)
            api_dict = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            cluster_id = f"{cluster.area_id} / {cluster.id}"
            body[cluster_id] = api_dict

            cluster_dict[cluster_id] = cluster

        updated_thermal_clusters = {}
        try:
            json_response = self._wrapper.put(url, json=body).json()

            for key, json_properties in json_response.items():
                if key in cluster_dict:  # Currently AntaresWeb returns all clusters not only the modified ones
                    api_properties = ThermalClusterPropertiesAPI.model_validate(json_properties)
                    thermal_properties = api_properties.to_user_model()
                    updated_thermal_clusters.update({cluster_dict[key]: thermal_properties})
        except APIError as e:
            raise ClustersPropertiesUpdateError(self.study_id, "thermal", e.message) from e

        return updated_thermal_clusters
