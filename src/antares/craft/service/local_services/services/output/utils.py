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

from antares.craft import Frequency


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


def normalize_df_column_names(mc_root: MCRoot, output_headers: list[list[str]]) -> list[str]:
    if mc_root == MCRoot.MC_IND:
        return [col[0] for col in output_headers]
    return [" ".join([col[0], col[2]]).upper().strip() for col in output_headers]


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


def parse_headers(content: str, start_col: int) -> list[list[str]]:
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
