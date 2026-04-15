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
from pathlib import Path

import pandas as pd

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import OutputDataRetrievalError, XpansionOutputParsingError
from antares.craft.model.output import AggregationEntry, Frequency, XpansionResult, XpansionSensitivityResult
from antares.craft.service.base_services import BaseOutputService
from antares.craft.service.local_services.services.output.output_aggregation import AggregatorManager, export_df_chunks
from antares.craft.service.output_matrix_parsing import read_output_matrix
from antares.craft.service.utils import read_ts_numbers_file
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

        dfs = aggregator_manager.aggregate_output_data()
        return export_df_chunks(self.config.study_path.parent, dfs)

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

    def _get_ts_numbers_path(self, output_id: str) -> Path:
        ts_numbers_path = self.config.study_path / "output" / output_id / "ts-numbers"
        if not ts_numbers_path.exists():
            raise OutputDataRetrievalError(output_id, "The `ts-numbers` folder does not exist")
        return ts_numbers_path

    @staticmethod
    def _read_ts_numbers_file(file_path: Path, output_id: str) -> dict[int, int]:
        if not file_path.exists():
            raise OutputDataRetrievalError(output_id, f"The file {file_path} does not exist")
        return read_ts_numbers_file(file_path)

    @override
    def get_solar_ts_numbers(self, area_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "solar" / f"{area_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_wind_ts_numbers(self, area_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "wind" / f"{area_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_load_ts_numbers(self, area_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "load" / f"{area_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_hydro_ts_numbers(self, area_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "hydro" / f"{area_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_link_ts_numbers(self, area_from: str, area_to: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "ntc" / area_from / f"{area_to}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_binding_constraint_ts_numbers(self, group_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "bindingconstraints" / f"{group_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_thermal_ts_numbers(self, area_id: str, thermal_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "thermal" / area_id / f"{thermal_id}.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_st_storage_inflows_numbers(self, area_id: str, st_storage_id: str, output_id: str) -> dict[int, int]:
        file_path = self._get_ts_numbers_path(output_id) / "st-storage" / area_id / st_storage_id / "inflows.txt"
        return self._read_ts_numbers_file(file_path, output_id)

    @override
    def get_st_storage_additional_constraints_numbers(
        self, area_id: str, st_storage_id: str, constraint_id: str, output_id: str
    ) -> dict[int, int]:
        file_path = (
            self._get_ts_numbers_path(output_id) / "st-storage" / area_id / st_storage_id / f"{constraint_id}.txt"
        )
        return self._read_ts_numbers_file(file_path, output_id)
