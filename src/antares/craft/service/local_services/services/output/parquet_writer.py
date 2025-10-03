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
from typing import Iterator

import pandas as pd
import pyarrow as pa

from pyarrow.parquet import ParquetFile, ParquetWriter


def _parquet_writer(output_file: Path, schema: pa.Schema) -> ParquetWriter:
    return ParquetWriter(output_file, schema, compression="zstd", data_page_version="2.0")


def write_dataframes_in_parquet_format_by_column_sets(
    path: Path, dataframes: Iterator[pd.DataFrame]
) -> tuple[list[Path], list[str]]:
    """
    Iterates over the given dataframes and writes them according to their given column sets.
    If 2 dataframes share the same columns, we write them in the same file.
    Everytime we encounter a new column sets, we create a new parquet file.

    Args:
        path: The parent folder path to write the parquet files into.
        dataframes: The dataframes to iterate over.

    Returns:
        A tuple containing:
        1- A list of all created parquet files
        2- The list of every column encountered in the given dataframes. To use when reindexing the dataframes.
    """
    file_paths = []
    current_writer = None
    try:
        first_df = next(dataframes)
        first_df.index = pd.RangeIndex(len(first_df))
        new_index = list(first_df.columns)
        existing_columns = set(new_index)

        file_path = path / "file0.parquet"
        file_paths.append(file_path)
        file_counter = 1

        table = pa.Table.from_pandas(first_df)
        current_schema = table.schema
        current_writer = _parquet_writer(file_path, current_schema)
        current_writer.write_table(table)

        while True:
            try:
                df = next(dataframes)
                should_write_new_file = False
                for col in df.columns:
                    if col not in existing_columns:
                        should_write_new_file = True
                        existing_columns.add(col)
                        new_index.append(col)

                df.index = pd.RangeIndex(len(df))

                if should_write_new_file:
                    current_writer.close()

                    file_path = path / f"file{file_counter}.parquet"
                    file_paths.append(file_path)
                    file_counter += 1

                    table = pa.Table.from_pandas(df)
                    current_schema = table.schema
                    current_writer = _parquet_writer(file_path, current_schema)
                else:
                    df = df.reindex(new_index, axis="columns")
                    # We're specifying the schema to use to be able to append NaN values to existing values.
                    table = pa.Table.from_pandas(df, schema=current_schema)

                current_writer.write_table(table)

            except StopIteration:
                return file_paths, new_index
    except StopIteration:
        return [], []
    finally:
        if current_writer:
            current_writer.close()


def yield_dataframes_from_parquet(files: list[Path], new_index: list[str]) -> pd.DataFrame:
    final_df = pd.DataFrame(columns=new_index)
    for file in files:
        parquet_file = ParquetFile(file)
        for i in range(parquet_file.num_row_groups):
            table = parquet_file.read_row_group(i)
            df = table.to_pandas()
            df = df.reindex(new_index, axis="columns")

            final_df = pd.concat([final_df, df])
    return final_df
