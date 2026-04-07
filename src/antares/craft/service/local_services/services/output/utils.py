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


class MCRoot(Enum):
    MC_IND = "mc-ind"
    MC_ALL = "mc-all"


def normalize_df_column_names(mc_root: MCRoot, output_headers: list[list[str]]) -> list[str]:
    if mc_root == MCRoot.MC_IND:
        return [col[0] for col in output_headers]
    return [" ".join([col[0], col[2]]).upper().strip() for col in output_headers]
