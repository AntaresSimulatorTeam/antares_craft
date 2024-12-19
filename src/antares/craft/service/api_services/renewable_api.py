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
from antares.craft.exceptions.exceptions import APIError, RenewableMatrixDownloadError, RenewablePropertiesUpdateError
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseRenewableService


class RenewableApiService(BaseRenewableService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    def update_renewable_properties(
        self, renewable_cluster: RenewableCluster, properties: RenewableClusterProperties
    ) -> RenewableClusterProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{renewable_cluster.area_id}/clusters/renewable/{renewable_cluster.id}"
        try:
            body = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not body:
                return renewable_cluster.properties

            response = self._wrapper.patch(url, json=body)
            json_response = response.json()
            del json_response["id"]
            del json_response["name"]
            new_properties = RenewableClusterProperties.model_validate(json_response)

        except APIError as e:
            raise RenewablePropertiesUpdateError(renewable_cluster.id, renewable_cluster.area_id, e.message) from e

        return new_properties

    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        try:
            path = PurePosixPath("input") / "renewables" / "series" / f"{area_id}" / f"{cluster_id}" / "series"
            return get_matrix(self._base_url, self.study_id, self._wrapper, path.as_posix())
        except APIError as e:
            raise RenewableMatrixDownloadError(area_id, cluster_id, e.message) from e

    def read_renewables(
        self,
        area_id: str,
    ) -> List[RenewableCluster]:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/renewable"
        json_renewables = self._wrapper.get(url).json()

        renewables = []

        for renewable in json_renewables:
            renewable_id = renewable.pop("id")
            renewable_name = renewable.pop("name")

            renewable_props = RenewableClusterProperties(**renewable)
            renewable_cluster = RenewableCluster(self.config, renewable_id, renewable_name, renewable_props)
            renewables.append(renewable_cluster)

        renewables.sort(key=lambda renewable: renewable.id)

        return renewables
