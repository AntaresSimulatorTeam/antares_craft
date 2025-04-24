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
import zipfile

from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft import LocalConfiguration
from antares.craft.exceptions.exceptions import MatrixDownloadError
from antares.craft.model.output import (
    Frequency,
    MCAllAreas,
    MCAllLinks,
    MCIndAreas,
    MCIndLinks,
    Output,
)
from antares.craft.service.local_services.factory import create_local_services

assets_dir = Path(__file__).parent / "assets"
ASSETS_DIR = Path(__file__).parent.resolve()

AREAS_REQUESTS__ALL = [
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES.value,
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.DETAILS.value,
            "frequency": "monthly",
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES.value,
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "OP. CoST,MRG. PrICE",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES.value,
            "frequency": "daily",
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES.value,
            "frequency": "monthly",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.ID.value,
            "frequency": "daily",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-06-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.VALUES.value,
            "frequency": "daily",
            "columns_names": "COsT,NoDU",
        },
        "test-07-all.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1427eco",
            "query_file": MCAllAreas.DETAILS.value,
            "frequency": "monthly",
            "columns_names": "COsT,NoDU",
        },
        "test-08-all.result.tsv",
    ),
]

LINKS_REQUESTS__ALL = [
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.VALUES.value,
            "frequency": "daily",
            "columns_names": "",
        },
        "test-01-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.VALUES.value,
            "frequency": "monthly",
            "columns_names": "",
        },
        "test-02-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.VALUES.value,
            "frequency": "daily",
            "columns_names": "",
        },
        "test-03-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.VALUES.value,
            "frequency": "monthly",
            "links_ids": "de - fr",
        },
        "test-04-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.ID.value,
            "frequency": "daily",
            "links_ids": "",
        },
        "test-05-all.result.tsv",
    ),
    (
        {
            "output_id": "20241807-1540eco-extra-outputs",
            "query_file": MCAllLinks.VALUES.value,
            "frequency": "daily",
            "columns_names": "MARG. COsT,CONG. ProB +",
        },
        "test-06-all.result.tsv",
    ),
]

WRONGLY_TYPED_REQUESTS__ALL = [
    {
        "output_id": "20201014-1427eco",
        "query_file": "fake_query_file",
        "frequency": "monthly",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1427eco",
        "query_file": "values",
        "frequency": "daily",
        "format": "fake_format",
    },
]

AREAS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.VALUES.value,
            "frequency": "hourly",
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.DETAILS.value,
            "frequency": "hourly",
            "mc_years": "1",
            "areas_ids": "de,fr,it",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.VALUES.value,
            "frequency": "weekly",
            "mc_years": "1,2",
            "areas_ids": "",
            "columns_names": "OP. COST,MRG. PRICE",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.VALUES.value,
            "frequency": "hourly",
            "mc_years": "2",
            "areas_ids": "es,fr,de",
            "columns_names": "",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.VALUES.value,
            "frequency": "annual",
            "mc_years": "",
            "areas_ids": "",
            "columns_names": "",
        },
        "test-05.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.VALUES.value,
            "frequency": "hourly",
            "columns_names": "COSt,NODu",
        },
        "test-06.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndAreas.DETAILS.value,
            "frequency": "hourly",
            "columns_names": "COSt,NODu",
        },
        "test-07.result.tsv",
    ),
]

LINKS_REQUESTS__IND = [
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinks.VALUES.value,
            "frequency": "hourly",
            "mc_years": "",
            "columns_names": "",
        },
        "test-01.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinks.VALUES.value,
            "frequency": "hourly",
            "mc_years": "1",
            "columns_names": "",
        },
        "test-02.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinks.VALUES.value,
            "frequency": "hourly",
            "mc_years": "1,2",
            "columns_names": "UCAP LIn.,FLOw qUAD.",
        },
        "test-03.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinks.VALUES.value,
            "frequency": "hourly",
            "mc_years": "1",
            "links_ids": "de - fr",
        },
        "test-04.result.tsv",
    ),
    (
        {
            "output_id": "20201014-1425eco-goodbye",
            "query_file": MCIndLinks.VALUES.value,
            "frequency": "hourly",
            "columns_names": "MArG. COsT,CONG. PRoB +",
        },
        "test-05.result.tsv",
    ),
]

WRONGLY_TYPED_REQUESTS__IND = [
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "fake_query_file",
        "frequency": "hourly",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "fake_frequency",
    },
    {
        "output_id": "20201014-1425eco-goodbye",
        "query_file": "values",
        "frequency": "hourly",
        "format": "fake_format",
    },
]


class TestOutput:
    def test_get_matrix_success(self, tmp_path, local_study):
        file_name = "details-hourly.txt"
        test_config = typing.cast(LocalConfiguration, local_study.service.config)
        services = create_local_services(test_config, "test-study")
        output_service = services.output_service
        output_1 = Output("output_1", False, output_service)
        def_path = tmp_path / "studyTest" / "output" / "output_1" / "economy"
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

    # TODO Antarest/examples/studies prendre outputs de STA-Mini prendre output et zipper code source
    # TODO reprendre les all.result.tsv dans /AntaREST/tests/integration/raw_studies_blueprint/assets/aggregate_areas_raw_data/test-01.result.tsv tu trouves les
    # TODO le path avec CONTROL N
    # TODO raw_study.synthesis.json pas besoin tu peux l'effacer :)

    def test_area_aggregate_mc_all(self, tmp_path):
        study_name = "test-study"

        config = LocalConfiguration(tmp_path, study_name)
        services = create_local_services(config, study_name)
        output_service = services.output_service

        for params, expected_result_filename in AREAS_REQUESTS__ALL:
            output_id = params["output_id"]
            frequency = Frequency(params["frequency"])
            query_file = params.get("query_file")
            mc_years = params.get("mc_years")
            areas_ids = params.get("areas_ids")
            columns_names = params.get("columns_names")

            zip_path = Path(assets_dir).joinpath("aggregate_areas_raw_data/output.zip")
            extract_path = tmp_path / study_name

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)

            output = Output(output_id, False, output_service)

            df = output.aggregate_areas_mc_all(
                query_file, frequency.value, areas_ids=areas_ids, columns_names=columns_names, mc_years=mc_years
            )

            resource_file = Path(ASSETS_DIR).joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)

            if not resource_file.exists() or resource_file.stat().st_size == 0:
                df.to_csv(resource_file, sep="\t", index=False)

            expected_df = pd.read_csv(resource_file, sep="\t", header=0).replace({np.nan: None})

            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)

            pd.testing.assert_frame_equal(df, expected_df)

            shutil.rmtree(extract_path)

    def test_area_aggregate_mc_ind(self, tmp_path):
        study_name = "test-study"

        config = LocalConfiguration(tmp_path, study_name)
        services = create_local_services(config, study_name)
        output_service = services.output_service

        for params, expected_result_filename in AREAS_REQUESTS__IND:
            output_id = params["output_id"]
            frequency = Frequency(params["frequency"])
            query_file = params.get("query_file")
            mc_years = params.get("mc_years")
            areas_ids = params.get("areas_ids")
            columns_names = params.get("columns_names")

            zip_path = Path(assets_dir).joinpath("aggregate_areas_raw_data/output.zip")
            extract_path = tmp_path / study_name

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)

            output = Output(output_id, False, output_service)

            df = output.aggregate_areas_mc_ind(
                query_file, frequency.value, areas_ids=areas_ids, columns_names=columns_names, mc_years=mc_years
            )

            resource_file = Path(ASSETS_DIR).joinpath(f"aggregate_areas_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)

            if not resource_file.exists() or resource_file.stat().st_size == 0:
                df.to_csv(resource_file, sep="\t", index=False)

            expected_df = pd.read_csv(resource_file, sep="\t", header=0).replace({np.nan: None})

            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)

            pd.testing.assert_frame_equal(df, expected_df)

            shutil.rmtree(extract_path)

    def test_link_aggregate_mc_all(self, tmp_path):
        study_name = "test-study"

        config = LocalConfiguration(tmp_path, study_name)
        services = create_local_services(config, study_name)
        output_service = services.output_service

        for params, expected_result_filename in LINKS_REQUESTS__ALL:
            output_id = params["output_id"]
            frequency = Frequency(params["frequency"])
            query_file = params.get("query_file")
            mc_years = params.get("mc_years")
            areas_ids = params.get("areas_ids")
            columns_names = params.get("columns_names")

            zip_path = Path(assets_dir).joinpath("aggregate_areas_raw_data/output.zip")
            extract_path = tmp_path / study_name

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)

            output = Output(output_id, False, output_service)

            df = output.aggregate_links_mc_all(
                query_file, frequency.value, areas_ids=areas_ids, columns_names=columns_names, mc_years=mc_years
            )

            resource_file = Path(ASSETS_DIR).joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)

            if not resource_file.exists() or resource_file.stat().st_size == 0:
                df.to_csv(resource_file, sep="\t", index=False)

            expected_df = pd.read_csv(resource_file, sep="\t", header=0).replace({np.nan: None})

            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)

            pd.testing.assert_frame_equal(df, expected_df)

            shutil.rmtree(extract_path)

    def test_link_aggregate_mc_ind(self, tmp_path):
        study_name = "test-study"

        config = LocalConfiguration(tmp_path, study_name)
        services = create_local_services(config, study_name)
        output_service = services.output_service

        for params, expected_result_filename in LINKS_REQUESTS__IND:
            output_id = params["output_id"]
            frequency = Frequency(params["frequency"])
            query_file = params.get("query_file")
            mc_years = params.get("mc_years")
            links_id = params.get("links_ids")
            columns_names = params.get("columns_names")

            zip_path = Path(assets_dir).joinpath("aggregate_areas_raw_data/output.zip")
            extract_path = tmp_path / study_name

            with zipfile.ZipFile(zip_path, "r") as zf:
                zf.extractall(extract_path)

            output = Output(output_id, False, output_service)

            df = output.aggregate_links_mc_ind(
                query_file, frequency.value, areas_ids=links_id, columns_names=columns_names, mc_years=mc_years
            )

            resource_file = Path(ASSETS_DIR).joinpath(f"aggregate_links_raw_data/{expected_result_filename}")
            resource_file.parent.mkdir(exist_ok=True, parents=True)

            if not resource_file.exists() or resource_file.stat().st_size == 0:
                df.to_csv(resource_file, sep="\t", index=False)

            expected_df = pd.read_csv(resource_file, sep="\t", header=0).replace({np.nan: None})

            for col in expected_df.columns:
                expected_df[col] = expected_df[col].astype(df[col].dtype)

            pd.testing.assert_frame_equal(df, expected_df)

            shutil.rmtree(extract_path)
