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

from antares import create_study_local
from antares.config.local_configuration import LocalConfiguration
from antares.model.area import Area
from antares.model.link import Link
from antares.model.study import Study
from antares.model.thermal import ThermalCluster


class TestLocalClient:
    def test_local_study(self, tmp_path):
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

        # Thermal
        fr_nuclear = fr.create_thermal_cluster("nuclear")

        assert isinstance(fr_nuclear, ThermalCluster)
