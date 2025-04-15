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
import pytest

import re

import numpy as np
import pandas as pd

from antares.craft.model.thermal import ThermalClusterPropertiesUpdate


class TestThermalTsGeneration:
    def test_nominal_case(self, local_study_w_thermals):
        # Change nominal capacity
        cluster_1 = local_study_w_thermals.get_areas()["fr"].get_thermals()["test thermal cluster"]
        cluster_2 = local_study_w_thermals.get_areas()["fr"].get_thermals()["thermal_fr_2"]
        cluster_3 = local_study_w_thermals.get_areas()["it"].get_thermals()["thermal_it"]
        for k, cluster in enumerate([cluster_1, cluster_2, cluster_3]):
            new_properties = ThermalClusterPropertiesUpdate(nominal_capacity=100 * (k + 1))
            cluster.update_properties(new_properties)
        # Generate new TS
        local_study_w_thermals.generate_thermal_timeseries(4)
        # Checks TS generated
        for k, cluster in enumerate([cluster_1, cluster_2, cluster_3]):
            series = cluster.get_series_matrix()
            expected_series = pd.DataFrame(np.full((8760, 4), (k + 1) * 100), dtype=np.int64)
            assert series.equals(expected_series)

    def test_error_case(self, local_study_w_thermals):
        with pytest.raises(
            ValueError,
            match=re.escape("Area fr, cluster test thermal cluster: Nominal power must be strictly positive, got 0."),
        ):
            local_study_w_thermals.generate_thermal_timeseries(4)
