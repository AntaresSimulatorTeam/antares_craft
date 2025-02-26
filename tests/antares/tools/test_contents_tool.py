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

import numpy as np
import pandas as pd

from antares.craft.tools.matrix_tool import prepare_args_replace_matrix, write_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType


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


def test_write_timeseries(tmpdir):
    file_path = Path(tmpdir)
    df = pd.DataFrame([1, 2, 3], columns=["Value"])

    write_timeseries(file_path, df, TimeSeriesFileType.THERMAL_MODULATION, area_id="fr", cluster_id="gaz")
    thermal_modulation_path = file_path / "input/thermal/prepro/fr/gaz/modulation.txt"
    assert thermal_modulation_path.exists()
    assert thermal_modulation_path.is_file()
    write_timeseries(file_path, df, TimeSeriesFileType.HYDRO_MAX_POWER, area_id="fr")
    hydro_max_power_path = file_path / "input/hydro/common/capacity/maxpower_fr.txt"
    assert hydro_max_power_path.exists()
    assert hydro_max_power_path.is_file()
    write_timeseries(file_path, df, TimeSeriesFileType.LINKS_CAPACITIES_DIRECT, area_id="fr", second_area_id="es")
    link_capacity_direct_path = file_path / "input/links/fr/capacities/es_direct.txt"
    assert link_capacity_direct_path.exists()
    assert link_capacity_direct_path.is_file()
    write_timeseries(file_path, df, TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL, constraint_id="constraint_1")
    thermal_modulation_path = file_path / "input/bindingconstraints/constraint_1_eq.txt"
    assert thermal_modulation_path.exists()
    assert thermal_modulation_path.is_file()
