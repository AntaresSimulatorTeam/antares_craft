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
from dataclasses import asdict
from pathlib import Path

from antares.craft import StudySettingsUpdate
from antares.craft.model.settings.general import GeneralParametersUpdate


def test_empty_scenariobuilder(local_study) -> None:
    sc_builder = local_study.get_scenario_builder()
    object_content = asdict(sc_builder)
    # Asserts the object is empty
    for value in object_content.values():
        assert value["_years"] == 1
        assert value["_data"] == {}


def test_scenario_builder(local_study_with_renewable) -> None:
    # Set the nb_years to 4
    local_study_with_renewable.update_settings(
        StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4))
    )
    # Create a scenario builder from scratch
    study_path = Path(local_study_with_renewable.path)
    ini_content = """[Default Ruleset]
hl,it,0 = 0.001
hl,it,1 = 0.002
hl,it,3 = 0.005
l,fr,0 = 1
l,fr,1 = 2
l,fr,2 = 3
l,fr,3 = 4
t,fr,0,test thermal cluster = 1
t,fr,1,test thermal cluster = 4
t,fr,2,test thermal cluster = 3
t,fr,3,test thermal cluster = 2"""
    sc_builder_path = study_path / "settings" / "scenariobuilder.dat"
    sc_builder_path.write_text(ini_content)
    # Reads the sc_builder
    sc_builder = local_study_with_renewable.get_scenario_builder()
    assert sc_builder.load.get_area("fr").get_scenario() == [1, 2, 3, 4]
    assert sc_builder.thermal.get_cluster("fr", "test thermal cluster").get_scenario() == [1, 4, 3, 2]
    assert sc_builder.hydro_initial_level.get_area("it").get_scenario() == [0.1, 0.2, None, 0.5]
