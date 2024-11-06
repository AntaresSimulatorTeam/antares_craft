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

from antares import create_study_local
from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import LinkCreationError
from antares.model.area import Area
from antares.model.link import Link
from antares.model.load import Load
from antares.model.study import Study
from antares.model.thermal import ThermalCluster


class TestLocalClient:
    def test_local_study(self, tmp_path, other_area):
        study_name = "test study"
        study_version = "880"
        study_config = LocalConfiguration(tmp_path, study_name)

        # Study
        test_study = create_study_local(study_name, study_version, study_config)
        assert isinstance(test_study, Study)

        # Areas
        fr = test_study.create_area("fr")
        at = test_study.create_area("at")

        assert isinstance(fr, Area)
        assert isinstance(at, Area)

        # Link
        at_fr = test_study.create_link(area_from=fr, area_to=at)

        assert isinstance(at_fr, Link)

        ## Cannot link areas that don't exist in the study
        with pytest.raises(LinkCreationError, match="Could not create the link fr / usa: usa does not exist."):
            test_study.create_link(area_from=fr, area_to=other_area)

        # Thermal
        fr_nuclear = fr.create_thermal_cluster("nuclear")

        assert isinstance(fr_nuclear, ThermalCluster)

        # Load
        time_series_rows = 365 * 24
        time_series_columns = 1
        load_time_series = pd.DataFrame(np.ones([time_series_rows, time_series_columns]))
        fr_load = fr.create_load(load_time_series)

        assert isinstance(fr_load, Load)

        expected_time_series = "1.0\n" * time_series_rows
        actual_time_series = fr_load.time_series.local_file.file_path.read_text()

        assert actual_time_series == expected_time_series
