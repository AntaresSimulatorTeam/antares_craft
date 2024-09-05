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

import numpy as np
import pandas as pd

from antares.tools.matrix_tool import prepare_args_replace_matrix


def test_prepare_args():
    # Given

    matrix = np.random.randint(0, 2, size=(8760, 1))
    series = pd.DataFrame(matrix, columns=["Value"])
    series_path = "input/thermal/series/area_id/cluster_name/series"

    # Expected result
    expected_result = {"action": "replace_matrix", "args": {"target": series_path, "matrix": matrix.tolist()}}

    # When
    result = prepare_args_replace_matrix(series, series_path)

    # Then
    assert result == expected_result
