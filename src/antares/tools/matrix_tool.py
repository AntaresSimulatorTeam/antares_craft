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
from pathlib import Path
from typing import Dict

import pandas as pd


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
