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
from io import StringIO

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import AggregateCreationError, APIError
from antares.craft.model.output import AggregationEntry
from antares.craft.service.api_services.utils import get_matrix
from antares.craft.service.base_services import BaseOutputService
from typing_extensions import override


class OutputApiService(BaseOutputService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def get_matrix(self, output_id: str, file_path: str) -> pd.DataFrame:
        full_path = f"output/{output_id}/economy/{file_path}"
        return get_matrix(self._base_url, self.study_id, self._wrapper, full_path)

    @override
    def aggregate_values(
        self, output_id: str, aggregation_entry: AggregationEntry, object_type: str, mc_type: str
    ) -> pd.DataFrame:
        url = f"{self._base_url}/studies/{self.study_id}/{object_type}/aggregate/mc-{mc_type}/{output_id}?{aggregation_entry.to_api_query(object_type)}"
        try:
            response = self._wrapper.get(url)
            return pd.read_csv(StringIO(response.text))
        except APIError as e:
            raise AggregateCreationError(self.study_id, output_id, mc_type, object_type, e.message)
