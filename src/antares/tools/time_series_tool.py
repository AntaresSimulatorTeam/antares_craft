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

from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd


class TimeSeriesFileType(Enum):
    """
    DTO for storing the paths to Antares time series files.

    This DTO contains the relative paths to different timeseries files used in the generation of an Antares study,
    starting from the base folder of the study.

    Files where the path contains {area_id} or {constraint_id} have to be used with `.format` to access the correct path.

    Example:
        TimeSeriesFileType.SOLAR.value.format(area_id="test_area")
    """

    BINDING_CONSTRAINT_EQUAL = Path("input") / "bindingconstraints" / "{constraint_id}_eq.txt"
    BINDING_CONSTRAINT_GREATER = Path("input") / "bindingconstraints" / "{constraint_id}_gt.txt"
    BINDING_CONSTRAINT_LESS = Path("input") / "bindingconstraints" / "{constraint_id}_lt.txt"
    LOAD = Path("input") / "load" / "series" / "load_{area_id}.txt"
    LOAD_CONVERSION = Path("input") / "load" / "prepro" / "{area_id}/conversion.txt"
    LOAD_DATA = Path("input") / "load" / "prepro" / "{area_id}" / "data.txt"
    LOAD_K = Path("input") / "load" / "prepro" / "{area_id}" / "k.txt"
    LOAD_TRANSLATION = Path("input") / "load" / "prepro" / "{area_id}" / "translation.txt"
    MISC_GEN = Path("input") / "misc-gen" / "miscgen-{area_id}.txt"
    RESERVES = Path("input") / "reserves" / "{area_id}.txt"
    SOLAR = Path("input") / "solar" / "series" / "solar_{area_id}.txt"
    SOLAR_CONVERSION = Path("input") / "solar" / "prepro" / "{area_id}" / "conversion.txt"
    SOLAR_DATA = Path("input") / "solar" / "prepro" / "{area_id}" / "data.txt"
    SOLAR_K = Path("input") / "solar" / "prepro" / "{area_id}" / "k.txt"
    SOLAR_TRANSLATION = Path("input") / "solar" / "prepro" / "{area_id}" / "translation.txt"
    WIND = Path("input") / "wind" / "series" / "wind_{area_id}.txt"
    WIND_CONVERSION = Path("input") / "wind" / "prepro" / "{area_id}" / "conversion.txt"
    WIND_DATA = Path("input") / "wind" / "prepro" / "{area_id}" / "data.txt"
    WIND_K = Path("input") / "wind" / "prepro" / "{area_id}" / "k.txt"
    WIND_TRANSLATION = Path("input") / "wind" / "prepro" / "{area_id}" / "translation.txt"

    def path(self) -> str:
        return str(self.value)


class TimeSeriesFile:
    """
    Handling time series files reading and writing locally.

    Time series are stored without headers in tab separated files, encoded with UTF-8.

    Args:
        ts_file_type: Type of time series file using the class TimeSeriesFileType.
        study_path: `Path` to the study directory.
        area_id: Area ID for file paths that use the area's id in their path
        constraint_id: Constraint ID for file paths that use the binding constraint's id in their path
        time_series: The actual timeseries as a pandas DataFrame.

    Raises:
        ValueError if the TimeSeriesFileType needs an area_id and none is provided.
    """

    def __init__(
        self,
        ts_file_type: TimeSeriesFileType,
        study_path: Path,
        *,
        area_id: Optional[str] = None,
        constraint_id: Optional[str] = None,
        time_series: Optional[pd.DataFrame] = None,
    ) -> None:
        ts_file_type_str = ts_file_type.path()
        if "{area_id}" in ts_file_type_str and area_id is None:
            raise ValueError("area_id is required for this file type.")
        if "{constraint_id}" in ts_file_type_str and constraint_id is None:
            raise ValueError("constraint_id is required for this file type.")

        self.file_path = study_path / (
            ts_file_type.value
            if not (area_id or constraint_id)
            else ts_file_type_str.format(area_id=area_id, constraint_id=constraint_id)
        )

        if self.file_path.is_file() and time_series is not None:
            raise ValueError(f"File {self.file_path} already exists and a time series was provided.")
        elif self.file_path.is_file() and time_series is None:
            self._time_series = pd.read_csv(self.file_path, sep="\t", header=None, index_col=None, encoding="utf-8")
        else:
            self._time_series = time_series if time_series is not None else pd.DataFrame([])
            self._write_file()

    @property
    def time_series(self) -> pd.DataFrame:
        return self._time_series

    @time_series.setter
    def time_series(self, time_series: pd.DataFrame) -> None:
        self._time_series = time_series
        self._write_file()

    def _write_file(self) -> None:
        self.file_path.parent.mkdir(parents=True, exist_ok=True)
        self._time_series.to_csv(self.file_path, sep="\t", header=False, index=False, encoding="utf-8")


class TimeSeries:
    """
    A time series for use in Antares

    Args:
        time_series: Pandas DataFrame containing the time series.
        local_file: TimeSeriesFile to store the time series if the study is local.
    """

    def __init__(
        self, time_series: pd.DataFrame = pd.DataFrame([]), local_file: Optional[TimeSeriesFile] = None
    ) -> None:
        self._time_series = time_series
        self._local_file = local_file

    @property
    def time_series(self) -> pd.DataFrame:
        return self._time_series

    @time_series.setter
    def time_series(self, time_series: pd.DataFrame) -> None:
        self._time_series = time_series
        if self._local_file is not None:
            self._local_file.time_series = time_series

    @property
    def local_file(self) -> Optional[TimeSeriesFile]:
        return self._local_file

    @local_file.setter
    def local_file(self, local_file: TimeSeriesFile) -> None:
        self._local_file = local_file
        self._time_series = local_file.time_series
