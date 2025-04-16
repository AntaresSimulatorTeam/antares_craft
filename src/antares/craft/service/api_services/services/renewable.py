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
    RenewableMatrixDownloadError,
    RenewableMatrixUpdateError,
)
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesUpdate
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import BaseRenewableService


class RenewableApiService(BaseRenewableService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def set_series(self, renewable_cluster: RenewableCluster, matrix: pd.DataFrame) -> None:
        try:
            path = (
                PurePosixPath("input")
                / "renewables"
                / "series"
                / f"{renewable_cluster.area_id}"
                / f"{renewable_cluster.id}"
                / "series"
            )

            update_series(self._base_url, self.study_id, self._wrapper, matrix, path.as_posix())
        except APIError as e:
            raise RenewableMatrixUpdateError(renewable_cluster.area_id, renewable_cluster.id, e.message) from e

    @override
    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        try:
            path = PurePosixPath("input") / "renewables" / "series" / f"{area_id}" / f"{cluster_id}" / "series"
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise RenewableMatrixDownloadError(area_id, cluster_id, e.message) from e

    @override
    def read_renewables(self) -> dict[str, dict[str, RenewableCluster]]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/renewables"
        json_renewable = self._wrapper.get(url).json()

        renewables: dict[str, dict[str, RenewableCluster]] = {}

        for key, renewable in json_renewable.items():
            area_id, renewable_id = key.split(" / ")
            api_props = RenewableClusterPropertiesAPI.model_validate(renewable)
            renewable_props = api_props.to_user_model()
            renewable_cluster = RenewableCluster(self, area_id, renewable_id, renewable_props)

            renewables.setdefault(area_id, {})[renewable_cluster.id] = renewable_cluster

        return renewables

    @override
    def update_renewable_clusters_properties(
        self, new_props: dict[RenewableCluster, RenewableClusterPropertiesUpdate]
    ) -> dict[RenewableCluster, RenewableClusterProperties]:
        url = f"{self._base_url}/studies/{self.study_id}/table-mode/renewables"
        body = {}
        cluster_dict = {}  # to fill the method's response
        updated_renewable_clusters = {}

        for cluster, props in new_props.items():
            api_properties = RenewableClusterPropertiesAPI.from_user_model(props)
            api_dict = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            cluster_id = f"{cluster.area_id} / {cluster.id}"
            body[cluster_id] = api_dict

            cluster_dict[cluster_id] = cluster

        try:
            json_response = self._wrapper.put(url, json=body).json()
            for key, json_properties in json_response.items():
                if key in cluster_dict:  # Currently AntaresWeb returns all clusters not only the modified ones
                    api_properties = RenewableClusterPropertiesAPI.model_validate(json_properties)
                    renewable_properties = api_properties.to_user_model()
                    updated_renewable_clusters.update({cluster_dict[key]: renewable_properties})

        except APIError as e:
            raise ClustersPropertiesUpdateError(self.study_id, "renewable", e.message) from e

        return updated_renewable_clusters
