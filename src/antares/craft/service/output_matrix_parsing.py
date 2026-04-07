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

from dataclasses import dataclass
from io import StringIO
from pathlib import Path
from typing import TypeAlias

import numpy as np
import pandas as pd
import polars as pl

from polars.exceptions import ComputeError

from antares.craft.model.output import Frequency

SingleOutputHeaders: TypeAlias = list[str]
MultipleOutputHeaders: TypeAlias = list[list[str]]


def parse_headers(content: str, start_col: int) -> MultipleOutputHeaders:
    lines = content.splitlines()
    header_lines = []
    for idx, line in enumerate(lines[4:7]):
        cols = line.split("\t")[start_col:]
        if idx == 0:
            header_lines = [[col] for col in cols]
        else:
            for k, col in enumerate(cols):
                header_lines[k].append(col)

    return header_lines


def _parse_output_dataframe(source: Path | StringIO) -> pl.DataFrame:
    try:
        return pl.read_csv(source, skip_lines=7, separator="\t", has_header=False, null_values="N/A", n_threads=1)
    except ComputeError:
        # Happens if polars wrongly inferred the schema.
        # If so, we specify that it should read the entire file to be sure it doesn't infer a false schema.
        # It's significantly slower but it does not fail.
        # As no file is longer than 10.000 rows we use this value.
        return pl.read_csv(
            source,
            skip_lines=7,
            separator="\t",
            has_header=False,
            null_values="N/A",
            infer_schema_length=10000,
            n_threads=1,
        )


def get_start_column(frequency: Frequency) -> int:
    if frequency == Frequency.ANNUAL:
        return 2
    elif frequency == Frequency.MONTHLY:
        return 3
    elif frequency == Frequency.WEEKLY:
        return 2
    elif frequency == Frequency.DAILY:
        return 4
    elif frequency == Frequency.HOURLY:
        return 5
    else:
        raise NotImplementedError(f"Unknown frequency {frequency.value}")


@dataclass
class OutputDataFrame:
    """
    We separate the polars dataframe and its headers as polars does not handle multi-headers columns.
    """

    data: pl.DataFrame
    headers: SingleOutputHeaders | MultipleOutputHeaders


def parse_output_file(source: Path | StringIO, first_column: int) -> OutputDataFrame:
    if isinstance(source, Path):
        content = source.read_text(encoding="utf-8")
    else:
        content = source.read()
        source.seek(0)

    output_headers = parse_headers(content, first_column)
    polars_df = _parse_output_dataframe(source)

    df = polars_df[polars_df.columns[first_column:]]

    # At this point we only have numeric values in our df. But NaN columns are considered to be String by polars.
    # So we change this to be Float64 to harmonize everything.
    df = df.with_columns(pl.col(pl.Utf8).cast(pl.Float64))

    return OutputDataFrame(data=df, headers=output_headers)


def read_output_matrix(source: Path | StringIO, frequency: Frequency) -> pd.DataFrame:
    output_first_column = get_start_column(frequency)
    output = parse_output_file(source, output_first_column)
    df = output.data.to_pandas().astype(np.float64)
    df.columns = pd.MultiIndex.from_tuples(output.headers)  # type: ignore
    return df
