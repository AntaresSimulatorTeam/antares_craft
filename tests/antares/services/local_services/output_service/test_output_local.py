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

import dataclasses
import typing
import zipfile

from pathlib import Path

import pandas as pd

from antares.craft import LocalConfiguration
from antares.craft.model.output import (
    Frequency,
    MCAllAreas,
    MCAllLinks,
    MCIndAreas,
    MCIndLinks,
    Output,
)
from antares.craft.service.local_services.factory import create_local_services

ASSETS_DIR = Path(__file__).parent / "assets"


@dataclasses.dataclass(frozen=True)
class TestParams:
    output_id: str
    query_file: str
    frequency: Frequency
    mc_years: list[str]
    type_ids: list[str]
    columns_names: list[str]


AREAS_REQUESTS__ALL = [
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.DETAILS.value,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=["de", "fr", "it"],
            columns_names=[],
        ),
        "test-02-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=["OP. CoST", "MRG. PrICE"],
        ),
        "test-03-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=["es", "fr", "de"],
            columns_names=[],
        ),
        "test-04-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.VALUES.value,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.ID.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-06-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=["COsT", "NoDU"],
        ),
        "test-07-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1427eco",
            query_file=MCAllAreas.DETAILS.value,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[],
            columns_names=["COsT", "NoDU"],
        ),
        "test-08-all.result.tsv",
    ),
]

LINKS_REQUESTS__ALL = [
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.VALUES.value,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-02-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-03-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.VALUES.value,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=["de - fr"],
            columns_names=[],
        ),
        "test-04-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.ID.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05-all.result.tsv",
    ),
    (
        TestParams(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinks.VALUES.value,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=["MARG. COsT", "CONG. ProB +"],
        ),
        "test-06-all.result.tsv",
    ),
]

AREAS_REQUESTS__IND = [
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.DETAILS.value,
            frequency=Frequency.HOURLY,
            mc_years=["1"],
            type_ids=["de", "fr", "it"],
            columns_names=[],
        ),
        "test-02-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.VALUES.value,
            frequency=Frequency.WEEKLY,
            mc_years=["1", "2"],
            type_ids=[],
            columns_names=["OP. COST", "MRG. PRICE"],
        ),
        "test-03-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=["2"],
            type_ids=["es", "fr", "de"],
            columns_names=[],
        ),
        "test-04-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.VALUES.value,
            frequency=Frequency.ANNUAL,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["COSt", "NODu"],
        ),
        "test-06-result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreas.DETAILS.value,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["COSt", "NODu"],
        ),
        "test-07-result.tsv",
    ),
]

LINKS_REQUESTS__IND = [
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinks.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinks.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=["1"],
            type_ids=[],
            columns_names=[],
        ),
        "test-02.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinks.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=["1", "2"],
            type_ids=[],
            columns_names=["UCAP LIn.", "FLOw qUAD."],
        ),
        "test-03.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinks.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=["1"],
            type_ids=["de - fr"],
            columns_names=[],
        ),
        "test-04.result.tsv",
    ),
    (
        TestParams(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinks.VALUES.value,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["MArG. COsT", "CONG. PRoB +"],
        ),
        "test-05.result.tsv",
    ),
]

# AREAS_REQUESTS__ALL = [
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.VALUES.value,
#             "frequency": "daily",
#             "areas_ids": [],
#             "columns_names": [],
#         },
#         "test-01-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.DETAILS.value,
#             "frequency": "monthly",
#             "areas_ids": ["de", "fr", "it"],
#             "columns_names": [],
#         },
#         "test-02-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.VALUES.value,
#             "frequency": "daily",
#             "areas_ids": [],
#             "columns_names": ["OP. CoST", "MRG. PrICE"],
#         },
#         "test-03-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.VALUES.value,
#             "frequency": "daily",
#             "areas_ids": ["es", "fr", "de"],
#             "columns_names": [],
#         },
#         "test-04-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.VALUES.value,
#             "frequency": "monthly",
#             "areas_ids": [],
#             "columns_names": [],
#         },
#         "test-05-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.ID.value,
#             "frequency": "daily",
#             "areas_ids": [],
#             "columns_names": [],
#         },
#         "test-06-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.VALUES.value,
#             "frequency": "daily",
#             "columns_names": ["COsT", "NoDU"],
#         },
#         "test-07-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1427eco",
#             "query_file": MCAllAreas.DETAILS.value,
#             "frequency": "monthly",
#             "columns_names": ["COsT", "NoDU"],
#         },
#         "test-08-all.result.tsv",
#     ),
# ]
#
# LINKS_REQUESTS__ALL = [
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.VALUES.value,
#             "frequency": "daily",
#             "columns_names": [],
#         },
#         "test-01-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.VALUES.value,
#             "frequency": "monthly",
#             "columns_names": [],
#         },
#         "test-02-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.VALUES.value,
#             "frequency": "daily",
#             "columns_names": [],
#         },
#         "test-03-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.VALUES.value,
#             "frequency": "monthly",
#             "links_ids": ["de - fr"],
#         },
#         "test-04-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.ID.value,
#             "frequency": "daily",
#             "links_ids": [],
#         },
#         "test-05-all.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20241807-1540eco-extra-outputs",
#             "query_file": MCAllLinks.VALUES.value,
#             "frequency": "daily",
#             "columns_names": ["MARG. COsT", "CONG. ProB +"],
#         },
#         "test-06-all.result.tsv",
#     ),
# ]
#
# AREAS_REQUESTS__IND = [
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": [],
#             "areas_ids": [],
#             "columns_names": [],
#         },
#         "test-01.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.DETAILS.value,
#             "frequency": "hourly",
#             "mc_years": ["1"],
#             "areas_ids": ["de", "fr", "it"],
#             "columns_names": [],
#         },
#         "test-02.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.VALUES.value,
#             "frequency": "weekly",
#             "mc_years": ["1", "2"],
#             "areas_ids": [],
#             "columns_names": ["OP. COST", "MRG. PRICE"],
#         },
#         "test-03.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": ["2"],
#             "areas_ids": ["es", "fr", "de"],
#             "columns_names": [],
#         },
#         "test-04.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.VALUES.value,
#             "frequency": "annual",
#             "mc_years": [],
#             "areas_ids": [],
#             "columns_names": [],
#         },
#         "test-05.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.VALUES.value,
#             "frequency": "hourly",
#             "columns_names": ["COSt", "NODu"],
#         },
#         "test-06.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndAreas.DETAILS.value,
#             "frequency": "hourly",
#             "columns_names": ["COSt", "NODu"],
#         },
#         "test-07.result.tsv",
#     ),
# ]
#
# LINKS_REQUESTS__IND = [
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndLinks.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": [],
#             "columns_names": [],
#         },
#         "test-01.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndLinks.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": ["1"],
#             "columns_names": [],
#         },
#         "test-02.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndLinks.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": ["1", "2"],
#             "columns_names": ["UCAP LIn.", "FLOw qUAD."],
#         },
#         "test-03.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndLinks.VALUES.value,
#             "frequency": "hourly",
#             "mc_years": ["1"],
#             "links_ids": ["de - fr"],
#         },
#         "test-04.result.tsv",
#     ),
#     (
#         {
#             "output_id": "20201014-1425eco-goodbye",
#             "query_file": MCIndLinks.VALUES.value,
#             "frequency": "hourly",
#             "columns_names": ["MArG. COsT", "CONG. PRoB +"],
#         },
#         "test-05.result.tsv",
#     ),
# ]


def setup_output(tmp_path, output_id: str) -> Output:
    study_name = "studyTest"
    config = LocalConfiguration(tmp_path, study_name)
    services = create_local_services(config, study_name)
    output_service = services.output_service

    zip_path = Path(ASSETS_DIR).joinpath("output.zip")
    extract_path = tmp_path / study_name

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    output = Output(output_id, False, output_service)

    return output


def update_expected_result_if_absent(resource_file, df):
    if not resource_file.exists() or resource_file.stat().st_size == 0:
        df.to_csv(resource_file, sep="\t", index=False)


class TestOutput:
    def test_get_matrix(self, tmp_path, local_study):
        file_name = "details-monthly.txt"
        output_name = "20201014-1427eco"

        test_config = typing.cast(LocalConfiguration, local_study.service.config)
        services = create_local_services(test_config, "studyTest")
        output_service = services.output_service

        output_1 = setup_output(tmp_path, output_name)
        file_path = Path(f"mc-all/areas/es/{file_name}")
        def_path = tmp_path / "studyTest" / "output" / output_name / "economy" / file_path

        expected_dataframe = pd.read_csv(
            def_path, sep="\t", skiprows=4, header=[0, 1, 2], na_values="N/A", float_precision="legacy"
        )
        dataframe = output_service.get_matrix(output_1.name, file_path.as_posix())
        assert dataframe.equals(expected_dataframe)

    @pytest.mark.parametrize("params,expected_result_filename", AREAS_REQUESTS__ALL)
    def test_area_aggregate_mc_all(self, tmp_path, params, expected_result_filename):
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_areas_mc_all(
            params.query_file,
            params.frequency.value,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_areas_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", AREAS_REQUESTS__IND)
    def test_area_aggregate_mc_ind(self, tmp_path, params, expected_result_filename):
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_areas_mc_ind(
            params.query_file,
            params.frequency.value,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_areas_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", LINKS_REQUESTS__ALL)
    def test_link_aggregate_mc_all(self, tmp_path, params, expected_result_filename):
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_links_mc_all(
            params.query_file,
            params.frequency.value,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_links_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", LINKS_REQUESTS__IND)
    def test_link_aggregate_mc_ind(self, tmp_path, params, expected_result_filename):
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_links_mc_ind(
            params.query_file,
            params.frequency.value,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_links_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)
