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
import zipfile

from enum import Enum
from pathlib import Path

import pandas as pd

from antares.craft import LocalConfiguration, Study
from antares.craft.model.output import (
    Frequency,
    MCAllAreasDataType,
    MCAllLinksDataType,
    MCIndAreasDataType,
    MCIndLinksDataType,
    Output,
)
from antares.craft.model.study import STUDY_VERSION_8_8
from antares.craft.service.local_services.factory import create_local_services
from antares.craft.service.utils import read_output_matrix

ASSETS_DIR = Path(__file__).parent / "assets"


@dataclasses.dataclass(frozen=True)
class TestParamsAreas:
    output_id: str
    query_file: Enum
    frequency: Frequency
    mc_years: list[int]
    type_ids: list[str]
    columns_names: list[str]


@dataclasses.dataclass(frozen=True)
class TestParamsLinks:
    output_id: str
    query_file: Enum
    frequency: Frequency
    mc_years: list[int]
    type_ids: list[tuple[str, str]]
    columns_names: list[str]


AREAS_REQUESTS__ALL = [
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.DETAILS,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=["de", "fr", "it"],
            columns_names=[],
        ),
        "test-02-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=["OP. CoST", "MRG. PrICE"],
        ),
        "test-03-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=["es", "fr", "de"],
            columns_names=[],
        ),
        "test-04-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.VALUES,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.ID,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-06-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=["COsT", "NoDU"],
        ),
        "test-07-all.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1427eco",
            query_file=MCAllAreasDataType.DETAILS,
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
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01-all.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.VALUES,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-02-all.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.VALUES,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-03-all.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.VALUES,
            frequency=Frequency.MONTHLY,
            mc_years=[],
            type_ids=[("de", "fr")],
            columns_names=[],
        ),
        "test-04-all.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.ID,
            frequency=Frequency.DAILY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05-all.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20241807-1540eco-extra-outputs",
            query_file=MCAllLinksDataType.VALUES,
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
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.DETAILS,
            frequency=Frequency.HOURLY,
            mc_years=[1],
            type_ids=["de", "fr", "it"],
            columns_names=[],
        ),
        "test-02.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.VALUES,
            frequency=Frequency.WEEKLY,
            mc_years=[1, 2],
            type_ids=[],
            columns_names=["OP. COST", "MRG. PRICE"],
        ),
        "test-03.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[2],
            type_ids=["es", "fr", "de"],
            columns_names=[],
        ),
        "test-04.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.VALUES,
            frequency=Frequency.ANNUAL,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-05.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["COSt", "NODu"],
        ),
        "test-06.result.tsv",
    ),
    (
        TestParamsAreas(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndAreasDataType.DETAILS,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["COSt", "NODu"],
        ),
        "test-07.result.tsv",
    ),
]

LINKS_REQUESTS__IND = [
    (
        TestParamsLinks(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinksDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=[],
        ),
        "test-01.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinksDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[1],
            type_ids=[],
            columns_names=[],
        ),
        "test-02.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinksDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[1, 2],
            type_ids=[],
            columns_names=["UCAP LIn.", "FLOw qUAD."],
        ),
        "test-03.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinksDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[1],
            type_ids=[("de", "fr")],
            columns_names=[],
        ),
        "test-04.result.tsv",
    ),
    (
        TestParamsLinks(
            output_id="20201014-1425eco-goodbye",
            query_file=MCIndLinksDataType.VALUES,
            frequency=Frequency.HOURLY,
            mc_years=[],
            type_ids=[],
            columns_names=["MArG. COsT", "CONG. PRoB +"],
        ),
        "test-05.result.tsv",
    ),
]


def setup_output(tmp_path: Path, output_id: str) -> Output:
    study_name = "studyTest"
    config = LocalConfiguration(tmp_path, study_name)
    services = create_local_services(config, study_name, STUDY_VERSION_8_8)
    output_service = services.output_service

    zip_path = Path(ASSETS_DIR).joinpath("output.zip")
    extract_path = tmp_path / study_name

    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_path)

    output = Output(output_id, False, output_service)

    return output


def update_expected_result_if_absent(resource_file: Path, df: pd.DataFrame) -> None:
    if not resource_file.exists() or resource_file.stat().st_size == 0:
        df.to_csv(resource_file, sep="\t", index=False)


class TestOutput:
    def test_get_matrix(self, tmp_path: Path, local_study: Study) -> None:
        file_name = "details-monthly.txt"
        output_name = "20201014-1427eco"

        output_1 = setup_output(tmp_path, output_name)

        # Area Part
        file_path = Path(f"mc-all/areas/es/{file_name}")
        matrix_path = tmp_path / "studyTest" / "output" / output_name / "economy" / file_path

        expected_dataframe = read_output_matrix(matrix_path, Frequency.MONTHLY)
        dataframe = output_1.get_mc_all_area(Frequency.MONTHLY, MCAllAreasDataType.DETAILS, "es")
        assert dataframe.equals(expected_dataframe)

        # Link Part
        output_name = "20201014-1422eco-hello"
        output_2 = setup_output(tmp_path, output_name)
        file_path = Path("mc-ind/00001/links/de - fr/values-hourly.txt")
        matrix_path = tmp_path / "studyTest" / "output" / output_name / "economy" / file_path
        expected_dataframe = read_output_matrix(matrix_path, Frequency.HOURLY)
        dataframe = output_2.get_mc_ind_link(1, Frequency.HOURLY, MCIndLinksDataType.VALUES, "fr", "de")
        assert dataframe.equals(expected_dataframe)

    @pytest.mark.parametrize("params,expected_result_filename", AREAS_REQUESTS__ALL)
    def test_area_aggregate_mc_all(
        self, tmp_path: Path, params: TestParamsAreas, expected_result_filename: str
    ) -> None:
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_mc_all_areas(
            MCAllAreasDataType(params.query_file),
            params.frequency,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_areas_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", AREAS_REQUESTS__IND)
    def test_area_aggregate_mc_ind(
        self, tmp_path: Path, params: TestParamsAreas, expected_result_filename: str
    ) -> None:
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_mc_ind_areas(
            MCIndAreasDataType(params.query_file),
            params.frequency,
            areas_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_areas_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", LINKS_REQUESTS__ALL)
    def test_link_aggregate_mc_all(
        self, tmp_path: Path, params: TestParamsLinks, expected_result_filename: str
    ) -> None:
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_mc_all_links(
            MCAllLinksDataType(params.query_file),
            params.frequency,
            links_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_links_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)

    @pytest.mark.parametrize("params,expected_result_filename", LINKS_REQUESTS__IND)
    def test_link_aggregate_mc_ind(
        self, tmp_path: Path, params: TestParamsLinks, expected_result_filename: str
    ) -> None:
        output = setup_output(tmp_path, params.output_id)

        df = output.aggregate_mc_ind_links(
            MCIndLinksDataType(params.query_file),
            params.frequency,
            links_ids=params.type_ids,
            columns_names=params.columns_names,
            mc_years=params.mc_years,
        )

        resource_file = Path(ASSETS_DIR) / "aggregate_links_raw_data" / expected_result_filename

        update_expected_result_if_absent(resource_file, df)

        expected_df = pd.read_csv(resource_file, sep="\t", header=0)

        pd.testing.assert_frame_equal(df, expected_df, check_dtype=False)
