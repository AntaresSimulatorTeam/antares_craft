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
from antares.exceptions.exceptions import AreaCreationError, LinkCreationError
from antares.model.area import Area
from antares.model.link import Link
from antares.model.study import Study
from antares.model.thermal import ThermalCluster
from antares.tools.time_series_tool import TimeSeriesFileType


class TestLocalClient:
    def test_local_study(self, tmp_path, other_area):
        study_name = "test study"
        study_version = "880"

        # Study
        test_study = create_study_local(study_name, study_version, tmp_path.absolute())
        assert isinstance(test_study, Study)

        # Areas
        fr = test_study.create_area("fr")
        at = test_study.create_area("at")

        assert isinstance(fr, Area)
        assert isinstance(at, Area)

        ## Area already exists
        with pytest.raises(
            AreaCreationError,
            match="Could not create the area fr: There is already an area 'fr' in the study 'test study'",
        ):
            test_study.create_area("fr")

        # Link
        at_fr = test_study.create_link(area_from=fr, area_to=at)

        assert isinstance(at_fr, Link)

        ## Cannot link areas that don't exist in the study
        with pytest.raises(LinkCreationError, match="Could not create the link fr / usa: usa does not exist."):
            test_study.create_link(area_from=fr, area_to=other_area)

        # Thermal
        fr_nuclear = fr.create_thermal_cluster("nuclear")

        assert isinstance(fr_nuclear, ThermalCluster)

        # Setup time series for following tests
        time_series_rows = 10  # 365 * 24
        time_series_columns = 1
        time_series = pd.DataFrame(np.around(np.random.rand(time_series_rows, time_series_columns)))

        # Load
        fr.create_load(time_series)

        assert test_study.service.config.study_path.joinpath(
            TimeSeriesFileType.LOAD.value.format(area_id=fr.id)
        ).is_file()

        fr_load = fr.get_load_matrix()

        assert fr_load.equals(time_series)

        # Solar
        fr.create_solar(time_series)

        assert test_study.service.config.study_path.joinpath(
            TimeSeriesFileType.SOLAR.value.format(area_id=fr.id)
        ).is_file()

        fr_solar = fr.get_solar_matrix()

        assert fr_solar.equals(time_series)
