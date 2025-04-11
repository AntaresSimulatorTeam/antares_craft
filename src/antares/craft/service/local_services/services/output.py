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
from antares.craft.exceptions.exceptions import MatrixDownloadError
from antares.craft.model.output import AggregationEntry
from antares.craft.service.base_services import BaseOutputService
from antares.craft.service.local_services.services.output_aggregation import AggregatorManager
from typing_extensions import override


class OutputLocalService(BaseOutputService):
    def __init__(self, config: LocalConfiguration, study_name: str) -> None:
        self.config = config
        self.study_name = study_name

    @override
    def get_matrix(self, output_id: str, file_path: str) -> pd.DataFrame:
        try:
            full_path = f"{self.config.study_path}/output/{output_id}/economy/{file_path}"
            dataframe = pd.read_csv(full_path)

        except FileNotFoundError as e:
            raise MatrixDownloadError(output_id, "output", file_path) from e
        return dataframe

    @override
    def aggregate_values(
        self, output_id: str, aggregation_entry: AggregationEntry, object_type: str, mc_type: str
    ) -> pd.DataFrame:
        aggregator_manager = AggregatorManager(
            self.config.study_path / "output" / output_id,
            aggregation_entry.query_file,
            aggregation_entry.frequency,
            aggregation_entry.type_ids,
            aggregation_entry.columns_names,
            aggregation_entry.mc_years,
        )

        df = aggregator_manager.aggregate_output_data()

        return df
