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
import pytest

from antares.tools.contents_tool import extract_content, retrieve_file_content
from antares.tools.matrix_tool import prepare_args_replace_matrix


def test_retrieve_file_content():
    # When
    area_content = retrieve_file_content("area_contents.json")

    # Then file is not empty
    assert len(area_content) > 0


def test_extract_content_key_not_defined():
    with pytest.raises(KeyError, match="Key 'nonexistent_key' not defined in area_contents.json"):
        extract_content("nonexistent_key", "area_contents.json")


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
