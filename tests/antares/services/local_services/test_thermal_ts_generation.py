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

import numpy as np
import pandas as pd

from antares.craft import Study
from antares.craft.model.thermal import ThermalClusterPropertiesUpdate


class TestThermalTsGeneration:
    def test_nominal_case(self, local_study_w_thermals: Study) -> None:
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

    def test_error_case(self, local_study_w_thermals: Study) -> None:
        thermal = local_study_w_thermals.get_areas()["it"].get_thermals()["thermal_it"]
        thermal.set_prepro_data(pd.DataFrame(np.full((365, 6), 12)))
        with pytest.raises(
            ValueError,
            match="Area it, cluster thermal_it: Forced failure rate is greater than 1 on following days",
        ):
            local_study_w_thermals.generate_thermal_timeseries(4)
