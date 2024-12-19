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
from typing import Dict, Optional

import pandas as pd

from antares.craft.tools.time_series_tool import TimeSeriesFileType


def prepare_args_replace_matrix(series: pd.DataFrame, series_path: str) -> Dict:
    """

    Args:
        series: matrix to be created in AntaresWeb with command "replace_matrix"
        series_path: Antares study path for matrix

    Returns:
        Dictionary containing command action and its arguments.
    """
    matrix = series.to_numpy().tolist()
    body = {"target": series_path, "matrix": matrix}
    return {"action": "replace_matrix", "args": body}


def df_save(df: pd.DataFrame, path: Path) -> None:
    df.to_csv(path, sep="\t", header=False, index=False, encoding="utf-8")


def df_read(path: Path) -> pd.DataFrame:
    return pd.read_csv(path, sep="\t", header=None)


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
        _time_series = df_read(file_path)
    else:
        _time_series = pd.DataFrame()

    return _time_series
