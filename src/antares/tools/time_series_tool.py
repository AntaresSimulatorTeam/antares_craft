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


class TimeSeries:
    """
    A time series for use in Antares

    Args:
        time_series: Pandas DataFrame containing the time series.
    """

    def __init__(self, time_series: pd.DataFrame = pd.DataFrame([])) -> None:
        self._time_series = time_series

    @property
    def time_series(self) -> pd.DataFrame:
        return self._time_series
