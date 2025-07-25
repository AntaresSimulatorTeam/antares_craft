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

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import XpansionOutputParsingError
from antares.craft.model.output import AggregationEntry, Frequency, XpansionResult, XpansionSensitivityResult
from antares.craft.service.base_services import BaseOutputService
from antares.craft.service.local_services.services.output.output_aggregation import AggregatorManager
from antares.craft.service.utils import read_output_matrix
from antares.craft.service.xpansion_output_parsing import parse_xpansion_out_json, parse_xpansion_sensitivity_out_json


class OutputLocalService(BaseOutputService):
    def __init__(self, config: LocalConfiguration, study_name: str) -> None:
        self.config = config
        self.study_name = study_name

    @override
    def get_matrix(self, output_id: str, file_path: str, frequency: Frequency) -> pd.DataFrame:
        full_path = self.config.study_path / "output" / output_id / "economy" / f"{file_path}.txt"
        return read_output_matrix(full_path, frequency)

    @override
    def aggregate_values(
        self, output_id: str, aggregation_entry: AggregationEntry, object_type: str, mc_type: str
    ) -> pd.DataFrame:
        type_ids = aggregation_entry.type_ids or []
        columns_names = aggregation_entry.columns_names or []
        mc_years = [int(mc_year) for mc_year in aggregation_entry.mc_years] if aggregation_entry.mc_years else []

        aggregator_manager = AggregatorManager(
            self.config.study_path / "output" / output_id,
            aggregation_entry.data_type,
            aggregation_entry.frequency,
            type_ids,
            columns_names,
            mc_years,
        )

        df = aggregator_manager.aggregate_output_data()

        return df

    @override
    def get_xpansion_result(self, output_id: str) -> XpansionResult:
        file_path = self.config.study_path / "output" / output_id / "expansion" / "out.json"
        try:
            return parse_xpansion_out_json(file_path.read_text())
        except Exception as e:
            raise XpansionOutputParsingError(self.study_name, output_id, "out.json", e.args[0])

    @override
    def get_xpansion_sensitivity_result(self, output_id: str) -> XpansionSensitivityResult:
        file_path = self.config.study_path / "output" / output_id / "sensitivity" / "sensitivity_out.json"
        try:
            return parse_xpansion_sensitivity_out_json(file_path.read_text())
        except Exception as e:
            raise XpansionOutputParsingError(self.study_name, output_id, "sensitivity_out.json", e.args[0])
