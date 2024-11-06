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
from antares.model.study import Study


class TestLocalClient:
    def test_local_study(self, tmp_path):
        study_name = "test study"
        study_version = "880"
        study_config = LocalConfiguration(tmp_path, study_name)

        # Study
        test_study = create_study_local(study_name, study_version, study_config)
        assert isinstance(test_study, Study)
