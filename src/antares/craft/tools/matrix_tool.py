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
        _time_series = pd.DataFrame()

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
