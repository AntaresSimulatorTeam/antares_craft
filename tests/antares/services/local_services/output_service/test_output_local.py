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

import pytest

import shutil
import typing

from pathlib import Path

import pandas as pd

from antares.craft import LocalConfiguration
from antares.craft.exceptions.exceptions import MatrixDownloadError
from antares.craft.model.output import Output, AggregationEntry
from antares.craft.service.local_services.factory import create_local_services

assets_dir = Path(__file__).parent / "assets"

class TestOutput:
    def test_get_matrix_success(self, tmp_path, local_study):
        file_name = "details-hourly.txt"
        test_config = typing.cast(LocalConfiguration, local_study.service.config)
        services = create_local_services(test_config, "test-study")
        output_service = services.output_service
        output_1 = Output("output_1", False, output_service)
        def_path = tmp_path / "studyTest" / "output_1" / "economy"
        shutil.copytree(assets_dir, def_path, dirs_exist_ok=True)
        expected_dataframe = pd.read_csv(assets_dir / file_name)
        dataframe = output_service.get_matrix(output_1.name, file_name)
        assert dataframe.equals(expected_dataframe)

    def test_get_matrix_fail(self, tmp_path, local_study):
        file_name = "details-hourly.txt"
        output_name = "output_1"
        test_config = typing.cast(LocalConfiguration, local_study.service.config)
        services = create_local_services(test_config, "test-study")
        output_service = services.output_service
        def_path = tmp_path / "studyTest" / output_name
        shutil.copytree(assets_dir, def_path, dirs_exist_ok=True)

        with pytest.raises(
            MatrixDownloadError, match=f"Error downloading output matrix for area {output_name}: {file_name}"
        ):
            output_service.get_matrix("output_1", file_name)

    def test_aggregation_links(self, tmp_path, local_study_w_output):
        test_config = typing.cast(LocalConfiguration, local_study_w_output.service.config)
        services = create_local_services(test_config, "test-study")
        output_service = services.output_service

        ind_def_path = Path("mc-ind") / "00001" / "links"
        all_def_path = Path("mc-all") / "links" / "alegro1 - alegro2"

        shutil.copytree(test_config.study_path, ind_def_path)

        output_service.aggregate_values()
    # def
