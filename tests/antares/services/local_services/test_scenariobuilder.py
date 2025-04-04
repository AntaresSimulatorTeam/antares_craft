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

from antares.craft.service.local_services.models.scenario_builder import ScenarioBuilderLocal
from antares.craft.tools.serde_local.ini_reader import IniReader


def test_scenariobuilder(tmp_path: Path) -> None:
    ini_content = """[Default Ruleset]
hl,be,0 = 0.001
hl,be,1 = 0.002
hl,be,3 = 0.005
l,fr,0 = 1
l,fr,1 = 2
l,fr,2 = 3
l,fr,3 = 4
t,fr,0,cluster_test = 1
t,fr,1,cluster_test = 4
t,fr,2,cluster_test = 3
t,fr,3,cluster_test = 2"""
    test_path = tmp_path / "test.txt"
    test_path.write_text(ini_content)
    content = IniReader().read(test_path)
    ScenarioBuilderLocal.from_ini(content)
