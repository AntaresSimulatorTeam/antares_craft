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

import numpy as np
import pandas as pd

from antares.tools.time_series_tool import TimeSeries, TimeSeriesFile, TimeSeriesFileType


class TestTimeSeries:
    def test_empty_ts_is_dataframe(self):
        # Given
        time_series = TimeSeries()

        assert isinstance(time_series.time_series, pd.DataFrame)
        assert time_series.time_series.empty
        assert time_series.time_series.equals(pd.DataFrame([]))

    def test_time_series_can_be_set(self, time_series_data):
        # Given
        time_series = TimeSeries()
        expected_time_series = pd.DataFrame(np.zeros(time_series_data.shape))

        # When
        time_series.time_series = time_series_data

        # Then
        assert time_series.time_series.equals(expected_time_series)

    def test_time_series_can_have_file(self, time_series_file):
        # Given
        time_series = TimeSeries()

        # When
        time_series.local_file = time_series_file

        # Then
        assert time_series.local_file.file_path.is_file()

    def test_time_series_can_update_file(self, time_series_file, time_series_data):
        # Given
        time_series = TimeSeries()
        expected_file_content = pd.DataFrame(np.zeros(time_series_data.shape))
        update_file_content = pd.DataFrame(np.ones(time_series_data.shape))

        # When
        time_series.local_file = time_series_file

        # Then
        assert time_series.time_series.equals(expected_file_content)

        # When
        time_series.time_series = update_file_content

        # Then
        actual_file_content = pd.read_csv(
            time_series.local_file.file_path, sep="\t", header=None, index_col=None, encoding="utf-8"
        )
        assert actual_file_content.equals(update_file_content)


class TestTimeSeriesFile:
    def test_time_series_file_can_be_set(self, time_series_file, time_series_data):
        # Given
        time_series = TimeSeries()

        # When
        time_series.local_file = time_series_file

        # Then
        assert time_series.time_series.equals(time_series_data)
        assert time_series_file.file_path.is_file()
        assert time_series.local_file is not None

    def test_time_series_file_time_series_can_be_updated(self, time_series_file, time_series_data):
        # Given
        time_series = TimeSeries(pd.DataFrame(np.ones([2, 3])))

        # When
        time_series_file.time_series = time_series.time_series

        with pytest.raises(AssertionError):
            assert time_series_file.time_series.equals(time_series_data)
        # assert time_series.local_file.file_path.is_file()
        assert time_series_file.time_series.equals(time_series.time_series)

    def test_no_area_provided_gives_error(self, tmp_path, time_series_data):
        # Given
        with pytest.raises(ValueError, match="area_id is required for this file type."):
            TimeSeriesFile(ts_file_type=TimeSeriesFileType.RESERVES, study_path=tmp_path, time_series=time_series_data)

    def test_file_exists_time_series_provided_gives_error(self, tmp_path, time_series_data):
        # Given
        time_series = TimeSeries(time_series_data)
        file_name = TimeSeriesFileType.RESERVES.value.format(area_id="test")

        # When
        (tmp_path / file_name).parent.mkdir(exist_ok=True, parents=True)
        time_series.time_series.to_csv(tmp_path / file_name, sep="\t", header=False, index=False, encoding="utf-8")

        # Then
        with pytest.raises(
            ValueError, match=f"File {tmp_path / file_name} already exists and a time series was provided."
        ):
            TimeSeriesFile(TimeSeriesFileType.RESERVES, tmp_path, area_id="test", time_series=time_series.time_series)

    def test_file_exists_no_time_series_provided(self, tmp_path, time_series_data):
        # Given
        time_series = TimeSeries(time_series_data)
        file_name = tmp_path / TimeSeriesFileType.RESERVES.value.format(area_id="test")

        # When
        file_name.parent.mkdir(exist_ok=True, parents=True)
        time_series.time_series.to_csv(file_name, sep="\t", header=False, index=False, encoding="utf-8")
        time_series_file = TimeSeriesFile(TimeSeriesFileType.RESERVES, tmp_path, area_id="test")

        # Then
        assert time_series_file.time_series.equals(time_series_data)
