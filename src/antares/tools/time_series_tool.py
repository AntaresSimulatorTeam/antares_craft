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
import os
from enum import Enum
from pathlib import Path
from typing import Optional

import pandas as pd


class TimeSeriesFileType(Enum):
    """
    The relative paths to different timeseries files used in the generation of an Antares study, starting from the
    base folder of the study.

    Files where the path contains {area_id} have to be used with .format(area_id=<area_id>) where <area_id> is the id
    in question to access the correct path.
    """

    MISC_GEN = "input/misc-gen/miscgen-{area_id}.txt"

    RESERVES = "input/reserves/{area_id}.txt"

    THERMAL_PREPRO_PREFIX = "input/thermal/prepro/{area_id}"
    THERMAL_MODULATION = "input/thermal/prepro/{area_id}/{group_id}/modulation.txt"
    THERMAL_DATA = "input/thermal/prepro/{area_id}/{group_id}/data.txt"
    THERMAL_SERIES_PREFIX = "input/thermal/series/{area_id}"
    THERMAL_DATA_SERIES = "input/thermal/series/{area_id}/{group_id}/series.txt"

    RENEWABLE_SERIES_PREFIX = "input/renewables/series/{area_id}"
    RENEWABLE_DATA_SERIES = "input/renewables/series/{area_id}/{group_id}/series.txt"

    LOAD_PREPRO_TRANSLATION = "input/load/prepro/{area_id}/translation.txt"
    LOAD_PREPRO_CONVERSION = "input/load/prepro/{area_id}/conversion.txt"
    LOAD_PREPRO_DATA = "input/load/prepro/{area_id}/data.txt"
    LOAD_PREPRO_K = "input/load/prepro/{area_id}/k.txt"
    LOAD_DATA_SERIES = "input/load/series/load_{area_id}.txt"

    SOLAR_PREPRO_TRANSLATION = "input/solar/prepro/{area_id}/translation.txt"
    SOLAR_PREPRO_CONVERSION = "input/solar/prepro/{area_id}/conversion.txt"
    SOLAR_PREPRO_DATA = "input/solar/prepro/{area_id}/data.txt"
    SOLAR_PREPRO_K = "input/solar/prepro/{area_id}/k.txt"
    SOLAR_DATA_SERIES = "input/solar/series/solar_{area_id}.txt"

    WIND_PREPRO_TRANSLATION = "input/wind/prepro/{area_id}/translation.txt"
    WIND_PREPRO_CONVERSION = "input/wind/prepro/{area_id}/conversion.txt"
    WIND_PREPRO_DATA = "input/wind/prepro/{area_id}/data.txt"
    WIND_PREPRO_K = "input/wind/prepro/{area_id}/k.txt"
    WIND_DATA_SERIES = "input/wind/series/wind_{area_id}.txt"


    HYDRO_COMMON_CM = "input/hydro/common/capacity/creditmodulations_{area_id}.txt"
    HYDRO_COMMON_IFP = "input/hydro/common/capacity/inflowPattern_{area_id}.txt"
    HYDRO_COMMON_MP = "input/hydro/common/capacity/maxpower_{area_id}.txt"
    HYDRO_COMMON_R = "input/hydro/common/capacity/reservoir_{area_id}.txt"
    HYDRO_COMMON_WV = "input/hydro/common/capacity/waterValues_{area_id}.txt"

    HYDRO_ENERGY = "input/hydro/prepro/{area_id}/energy.txt"

    HYDRO_MINGEN_SERIES = "input/hydro/series/{area_id}/mingen.txt"
    HYDRO_MOD_SERIES = "input/hydro/series/{area_id}/mod.txt"
    HYDRO_ROR_SERIES = "input/hydro/series/{area_id}/ror.txt"


class TimeSeriesFile:
    """
    Handling time series files reading and writing locally.

    Time series are stored without headers in tab separated files, encoded with UTF-8.

    Args:
        ts_file_type: Type of time series file using the class TimeSeriesFileType.
        study_path: `Path` to the study directory.
        area_id: Area ID for file paths that use the area's id in their path
        time_series: The actual timeseries as a pandas DataFrame.

    Raises:
        ValueError if the TimeSeriesFileType needs an area_id and none is provided.
    """

    def __init__(
        self,
        ts_file_type: TimeSeriesFileType,
        study_path: Path,
        area_id: Optional[str] = None,
        group_id: Optional[str] = None,
        time_series: Optional[pd.DataFrame] = None,
    ) -> None:
        if "{area_id}" in ts_file_type.value and area_id is None:
            raise ValueError("area_id is required for this file type.")
        if "{group_id}" in ts_file_type.value and group_id is None:
            raise ValueError("group_id is required for this file type.")
        if group_id:
            self.file_path = study_path / (
                ts_file_type.value
                if not area_id
                else ts_file_type.value.format(area_id=area_id, group_id=group_id)
            )
        else:
            self.file_path = study_path / (
                ts_file_type.value
                if not area_id
                else ts_file_type.value.format(area_id=area_id)
            )

        if self.file_path.is_file() and time_series is not None:
            raise ValueError(
                f"File {self.file_path} already exists and a time series was provided."
            )
        elif self.file_path.is_file() and time_series is None:

            if os.path.getsize(self.file_path) != 0:
                self._time_series = pd.read_csv(
                    self.file_path,
                    sep="\t",
                    header=None,
                    index_col=None,
                    encoding="utf-8",
                )
            else:
                self._time_series = pd.DataFrame()
        else:
            self._time_series = (
                time_series if time_series is not None else pd.DataFrame([])
            )
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
        self._time_series.to_csv(
            self.file_path, sep="\t", header=False, index=False, encoding="utf-8"
        )


class TimeSeries:
    """
    A time series for use in Antares
    """

    def __init__(
        self,
        time_series: pd.DataFrame = pd.DataFrame([]),
        local_file: Optional[TimeSeriesFile] = None,
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
