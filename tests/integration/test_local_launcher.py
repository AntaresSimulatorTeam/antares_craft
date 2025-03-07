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

from pathlib import Path

from antares.craft import create_study_local
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError


class TestLocalLauncher:
    def test_lifecycle(self, tmp_path: Path):
        study = create_study_local("test study", "880", tmp_path)
        with pytest.raises(
            AntaresSimulationRunningError,
            match=re.escape("Could not run the simulation for study test study: No solver path was provided"),
        ):
            study.run_antares_simulation()
