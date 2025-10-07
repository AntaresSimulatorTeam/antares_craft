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

from dataclasses import asdict
from pathlib import Path

from antares.craft import Study, StudySettingsUpdate
from antares.craft.exceptions.exceptions import InvalidFieldForVersionError
from antares.craft.model.commons import STUDY_VERSION_9_2, STUDY_VERSION_9_3
from antares.craft.model.settings.general import GeneralParametersUpdate


def test_empty_scenariobuilder(local_study: Study) -> None:
    sc_builder = local_study.get_scenario_builder()
    object_content = asdict(sc_builder)
    # Asserts the object is empty
    for key, value in object_content.items():
        if key in ("hydro_final_level", "storage_inflows", "storage_constraints"):
            assert value is None
        else:
            assert value["_years"] == 1
            assert value["_data"] == {}


def test_scenario_builder_lifecycle(local_study_with_renewable: Study) -> None:
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
    # Edits it
    sc_builder.renewable.get_cluster("fr", "renewable cluster").set_new_scenario([None, None, 2, 4])
    sc_builder.link.get_link("at / fr").set_new_scenario([4, 3, 2, 1])
    sc_builder.load.get_area("at").set_new_scenario([None, None, None, 1])
    local_study_with_renewable.set_scenario_builder(sc_builder)
    # Read it again to assert everything went well
    new_sc_builder = local_study_with_renewable.get_scenario_builder()
    assert new_sc_builder.load.get_area("fr").get_scenario() == [1, 2, 3, 4]
    assert new_sc_builder.thermal.get_cluster("fr", "test thermal cluster").get_scenario() == [1, 4, 3, 2]
    assert new_sc_builder.hydro_initial_level.get_area("it").get_scenario() == [0.1, 0.2, None, 0.5]
    assert new_sc_builder.link.get_link("at / fr").get_scenario() == [4, 3, 2, 1]
    assert new_sc_builder.load.get_area("at").get_scenario() == [None, None, None, 1]
    # Checks the ini content
    new_content = sc_builder_path.read_text()
    assert (
        new_content
        == """[Default Ruleset]
l,fr,0 = 1
l,fr,1 = 2
l,fr,2 = 3
l,fr,3 = 4
l,at,3 = 1
t,fr,0,test thermal cluster = 1
t,fr,1,test thermal cluster = 4
t,fr,2,test thermal cluster = 3
t,fr,3,test thermal cluster = 2
ntc,at,fr,0 = 4
ntc,at,fr,1 = 3
ntc,at,fr,2 = 2
ntc,at,fr,3 = 1
r,fr,2,renewable cluster = 2
r,fr,3,renewable cluster = 4
hl,it,0 = 0.001
hl,it,1 = 0.002
hl,it,3 = 0.005

"""
    )


def test_scenario_builder_version(local_study_with_renewable: Study, local_study_92: Study, local_study_93: Study) -> None:
    for study in (local_study_with_renewable, local_study_92, local_study_93):
        # Set the nb_years to 4
        study.update_settings(StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=4)))

        # Create a scenario builder with hydro_final_level
        study_path = Path(study.path)
        ini_content = """[Default Ruleset]
hfl,it,0 = 0.001
hfl,it,1 = 0.002
hfl,it,3 = 0.005"""
        sc_builder_path = study_path / "settings" / "scenariobuilder.dat"
        sc_builder_path.write_text(ini_content)

        if study._version < STUDY_VERSION_9_2:
            with pytest.raises(
                InvalidFieldForVersionError, match=re.escape("`hydro_final_level` only exists for v9.2+ studies")
            ):
                study.get_scenario_builder()

        else:
            sc_builder = study.get_scenario_builder()
            assert sc_builder.hydro_final_level is not None
            assert sc_builder.hydro_final_level.get_area("it").get_scenario() == [0.001, 0.002, None, 0.005]

        # Create a scenario builder with storage inflows and storage constraints
        # First create a storage with a constraint
        sts = study.get_areas()["fr"].create_st_storage("battery")
        # sts_constraint = [STStorageAdditionalConstraint(name="c1", occurrences=[Occurrence([1, 3])])]
        # sts.create_constraints(sts_constraint)

        ini_content = """[Default Ruleset]
        sts,fr,1,battery = 2
        sts,fr,2,battery = 3"""
        sc_builder_path.write_text(ini_content)

        if study._version < STUDY_VERSION_9_3:
            with pytest.raises(
                InvalidFieldForVersionError, match=re.escape("`storage_inflows` only exists for v9.3+ studies")
            ):
                study.get_scenario_builder()

        else:
            sc_builder = study.get_scenario_builder()
            assert sc_builder.storage_inflows is not None
            assert sc_builder.storage_inflows.get_storage("fr", "battery").get_scenario() == [None, 2, 3, None]
