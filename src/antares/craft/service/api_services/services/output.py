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
from pathlib import Path

import pandas as pd

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import AggregateCreationError, APIError
from antares.craft.model.output import AggregationEntry, Frequency
from antares.craft.service.base_services import BaseOutputService
from antares.craft.service.utils import read_output_matrix


class OutputApiService(BaseOutputService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def get_matrix(self, output_id: str, file_path: str, frequency: Frequency) -> pd.DataFrame:
        api_path = self._convert_path_for_web(file_path)
        full_path = f"output/{output_id}/economy/{api_path}"

        raw_url = f"{self._base_url}/studies/{self.study_id}/raw/original-file?path={full_path}"
        response = self._wrapper.get(raw_url)
        data = StringIO(response.text)

        return read_output_matrix(data, frequency)

    @staticmethod
    def _convert_path_for_web(file_path: str) -> str:
        # Note: AntaresWeb being completely stupid, it changed the path for links so we have to handle this case here ...
        parts = Path(file_path).parts
        if parts[0] == "mc-all" and parts[1] == "links":
            index = 2
        elif parts[0] == "mc-ind" and parts[2] == "links":
            index = 3
        else:
            return file_path

        local_formatting = parts[index].split(" - ")
        api_formatting = f"{local_formatting[0]}/{local_formatting[1]}"
        api_parts = list(parts)
        api_parts[index] = api_formatting
        return "/".join(api_parts)

    @override
    def aggregate_values(
        self, output_id: str, aggregation_entry: AggregationEntry, object_type: str, mc_type: str
    ) -> pd.DataFrame:
        url = f"{self._base_url}/studies/{self.study_id}/{object_type}/aggregate/mc-{mc_type}/{output_id}?{aggregation_entry.to_api_query(object_type)}"
        try:
            download_id = self._wrapper.get(url).json()
            metadata_url = f"{self._base_url}/downloads/{download_id}/metadata?wait_for_availability=True"
            # Wait for the aggregation to end
            self._wrapper.get(metadata_url)

            # Returns the aggregation
            download_url = f"{self._base_url}/downloads/{download_id}"
            aggregate = self._wrapper.get(download_url)
            return pd.read_csv(StringIO(aggregate.text))

        except APIError as e:
            raise AggregateCreationError(self.study_id, output_id, mc_type, object_type, e.message)
