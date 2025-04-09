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
import json
from unittest.mock import patch

import numpy as np
import pytest

import shutil
import typing

from pathlib import Path

import pandas as pd
from jinja2.lexer import TOKEN_DOT

from antares.craft import LocalConfiguration
from antares.craft.exceptions.exceptions import MatrixDownloadError
from antares.craft.model.output import Output, AggregationEntry, MCAllAreas, Frequency
from antares.craft.service.local_services.factory import create_local_services
from antares.craft.service.local_services.services.output_aggregation import AggregatorManager


assets_dir = Path(__file__).parent / "assets"
ASSETS_DIR = Path(__file__).parent.resolve()
AREAS_REQUESTS__ALL = [
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES,
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": MCAllAreas.DETAILS,
    #         "frequency": "monthly",
    #         "areas_ids": "de,fr,it",
    #         "columns_names": "",
    #     },
    #     "test-02-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "values",
    #         "frequency": "daily",
    #         "areas_ids": "",
    #         "columns_names": "OP. CoST,MRG. PrICE",
    #     },
    #     "test-03-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "values",
    #         "frequency": "daily",
    #         "areas_ids": "es,fr,de",
    #         "columns_names": "",
    #     },
    #     "test-04-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "values",
    #         "frequency": "monthly",
    #         "areas_ids": "",
    #         "columns_names": "",
    #     },
    #     "test-05-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "id",
    #         "frequency": "daily",
    #         "areas_ids": "",
    #         "columns_names": "",
    #     },
    #     "test-06-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "values",
    #         "frequency": "daily",
    #         "columns_names": "COsT,NoDU",
    #     },
    #     "test-07-all.result.tsv",
    # ),
    # (
    #     {
    #         "output_id": "20201014-1427eco",
    #         "query_file": "details",
    #         "frequency": "monthly",
    #         "columns_names": "COsT,NoDU",
    #     },
    #     "test-08-all.result.tsv",
    # ),
]

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

    # def


def test_aggregate_values_with_area_query():

    study_path = Path("/tmp/test-study-areas")
    study_name = "test-study-areas"



    config = LocalConfiguration(local_path=study_path, study_name=study_name)
    services = create_local_services(config, "test-study-areas")
    output_service = services.output_service


    output = Output(name="test-output", output_service=output_service, archived=False)

    expected_df = pd.DataFrame({
        "area": ["be", "fr"],
        "mcYear": [2012, 2013],
        "LOAD": [1000, 2000],
    })


    with patch.object(AggregatorManager, 'aggregate_output_data', return_value=expected_df) as mock_aggregate:
        df = output.aggregate_areas_mc_all(MCAllAreas.VALUES, "annual")


        mock_aggregate.assert_called_once()
        pd.testing.assert_frame_equal(df, expected_df)

#TODO Antarest/examples/studies prendre outputs de STA-Mini prendre output et zipper code source
#TODO reprendre les all.result.tsv dans /AntaREST/tests/integration/raw_studies_blueprint/assets/aggregate_areas_raw_data/test-01.result.tsv tu trouves les
#TODO le path avec CONTROL N
#TODO raw_study.synthesis.json pas besoin tu peux l'effacer :)
def test_area_aggregation_all():
    """
    Test the aggregation of areas data
    """
    study_path = Path("/tmp/test-study-areas")
    study_name = "test-study-areas"

    config = LocalConfiguration(local_path=study_path, study_name=study_name)
    services = create_local_services(config, study_name)
    output_service = services.output_service

    # Raw study for test
    # assets_path = Path("assets/test_synthesis/raw_study.synthesis.json")
    # with open(assets_path, "r") as f:
    #     raw_data = json.load(f)

    # outputs = raw_data.get("outputs", {})

    for params, expected_result_filename in AREAS_REQUESTS__ALL:
        output_id = params.pop("output_id")

        output_data = outputs.get(output_id)
        if not output_data:
            raise ValueError(f"Output with id {output_id} not found in the data file")

        mc_ind_path = (
            study_path
            / study_name
            / "output"
            / output_id
            / "economy"
            / "mc-ind"
        )
        mc_ind_path.mkdir(parents=True, exist_ok=True)

        for area in ["fr", "be"]:
            mc_all_path = (
                    study_path
                    / study_name
                    / "output"
                    / output_id
                    / "economy"
                    / "mc-all"
                    / "areas"
                    / area
            )
            mc_all_path.mkdir(parents=True, exist_ok=True)
            #dummy_file_src = Path("assets/values-daily.txt")
            dummy_file_src = Path("assets/values-daily.txt")
            dummy_file_dst = mc_all_path / dummy_file_src.name
            shutil.copy(dummy_file_src, dummy_file_dst)


        output = Output(
            name=output_id,
            output_service=output_service,
            archived=output_data.get("archived", False)
        )

        frequency = Frequency[params["frequency"].upper()]

        aggregation_entry = AggregationEntry(
            query_file=params.get("query_file"),
            frequency=frequency,
            mc_years=params.get("mc_years", []),
            type_ids=params.get("areas_ids", "").split(",") if "areas_ids" in params else [],
            columns_names=params["columns_names"].split(",") if "columns_names" in params else [],
        )


        df = output.aggregate_areas_mc_all(MCAllAreas.VALUES, aggregation_entry.frequency.value)

        # Expected result file path
        resource_file = Path("ASSETS_DIR").joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
        resource_file.parent.mkdir(exist_ok=True, parents=True)

        if not resource_file.exists() or resource_file.stat().st_size == 0:
            df.to_csv(resource_file, sep="\t", index=False)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0).replace({np.nan: None})

        for col in expected_df.columns:
            expected_df[col] = expected_df[col].astype(df[col].dtype)

        pd.testing.assert_frame_equal(df, expected_df)