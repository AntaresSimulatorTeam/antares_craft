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

from pathlib import Path
from typing import Optional

import pandas as pd

from antares.craft.tools.time_series_tool import TimeSeriesFileType

DEFAULT_MATRIX_MAPPING = {
    TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL: pd.DataFrame(),
    TimeSeriesFileType.BINDING_CONSTRAINT_GREATER: pd.DataFrame(),
    TimeSeriesFileType.BINDING_CONSTRAINT_LESS: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_MAX_POWER: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_RESERVOIR: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_INFLOW_PATTERN: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_CREDITS_MODULATION: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_WATER_VALUES: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_ROR: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_MOD: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_MINGEN: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_ENERGY: pd.DataFrame(),
    TimeSeriesFileType.LINKS_CAPACITIES_DIRECT: pd.DataFrame(),
    TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT: pd.DataFrame(),
    TimeSeriesFileType.LINKS_PARAMETERS: pd.DataFrame(),
    TimeSeriesFileType.LOAD: pd.DataFrame(),
    TimeSeriesFileType.MISC_GEN: pd.DataFrame(),
    TimeSeriesFileType.RENEWABLE_DATA_SERIES: pd.DataFrame(),
    TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION: pd.DataFrame(),
    TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL: pd.DataFrame(),
    TimeSeriesFileType.ST_STORAGE_INFLOWS: pd.DataFrame(),
    TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE: pd.DataFrame(),
    TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE: pd.DataFrame(),
    TimeSeriesFileType.RESERVES: pd.DataFrame(),
    TimeSeriesFileType.SOLAR: pd.DataFrame(),
    TimeSeriesFileType.THERMAL_SERIES: pd.DataFrame(),
    TimeSeriesFileType.THERMAL_DATA: pd.DataFrame(),
    TimeSeriesFileType.THERMAL_MODULATION: pd.DataFrame(),
    TimeSeriesFileType.THERMAL_CO2: pd.DataFrame(),
    TimeSeriesFileType.THERMAL_FUEL: pd.DataFrame(),
    TimeSeriesFileType.WIND: pd.DataFrame(),
}


def read_timeseries(
    ts_file_type: TimeSeriesFileType,
    study_path: Path,
    area_id: Optional[str] = None,
    constraint_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    second_area_id: Optional[str] = None,
) -> pd.DataFrame:
    file_path = study_path / (
        ts_file_type.value
        if not (area_id or constraint_id or cluster_id or second_area_id)
        else ts_file_type.value.format(
            area_id=area_id, constraint_id=constraint_id, cluster_id=cluster_id, second_area_id=second_area_id
        )
    )
    if os.path.getsize(file_path) != 0:
        _time_series = pd.read_csv(file_path, sep="\t", header=None)
    else:
        _time_series = pd.DataFrame(DEFAULT_MATRIX_MAPPING[ts_file_type])

    return _time_series


def write_timeseries(
    study_path: Path,
    series: Optional[pd.DataFrame],
    ts_file_type: TimeSeriesFileType,
    area_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    second_area_id: Optional[str] = None,
    constraint_id: Optional[str] = None,
) -> None:
    series = pd.DataFrame() if series is None else series
    format_kwargs = {}
    if area_id:
        format_kwargs["area_id"] = area_id
    if cluster_id:
        format_kwargs["cluster_id"] = cluster_id
    if second_area_id:
        format_kwargs["second_area_id"] = second_area_id
    if constraint_id:
        format_kwargs["constraint_id"] = constraint_id

    file_path = study_path / ts_file_type.value.format(**format_kwargs)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    series.to_csv(file_path, sep="\t", header=False, index=False, encoding="utf-8")
