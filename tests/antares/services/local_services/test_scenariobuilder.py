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

from antares.craft import (
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    Occurrence,
    STStorageAdditionalConstraint,
    Study,
    StudySettingsUpdate,
)
from antares.craft.exceptions.exceptions import InvalidFieldForVersionError
from antares.craft.model.commons import STUDY_VERSION_9_2, STUDY_VERSION_9_3
from antares.craft.model.settings.general import GeneralParametersUpdate
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


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


def test_scenario_builder_version(
    local_study_with_renewable: Study, local_study_92: Study, local_study_93: Study
) -> None:
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

        # Create a scenario builder with storage inflows
        sts = study.get_areas()["fr"].create_st_storage("battery")

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

            # Create constraint
            sts_constraint = [STStorageAdditionalConstraint(name="c1", occurrences=[Occurrence([1, 3])])]
            sts.create_constraints(sts_constraint)

            # Crate a scenario builder with storage constraints
            sc_builder = study.get_scenario_builder()
            assert sc_builder.storage_constraints is not None
            sc_builder.storage_constraints.get_constraint("fr", "battery", "c1").set_new_scenario([1, None, 4, None])

            study.set_scenario_builder(sc_builder)

            # Reads the ini content
            expected_ini_content = """[Default Ruleset]
sts,fr,1,battery = 2
sts,fr,2,battery = 3
sta,fr,0,battery,c1 = 1
sta,fr,2,battery,c1 = 4

"""
            assert sc_builder_path.read_text() == expected_ini_content

            sc_builder = study.get_scenario_builder()
            assert sc_builder.storage_constraints is not None
            assert sc_builder.storage_constraints.get_constraint("fr", "battery", "c1").get_scenario() == [
                1,
                None,
                4,
                None,
            ]


def test_scenario_builder_cluster_removals(local_study_with_renewable: Study) -> None:
    area_fr = local_study_with_renewable.get_areas()["fr"]
    # Creates a scenario builder with thermal and renewable data
    file_path = Path(local_study_with_renewable.path) / "settings" / "scenariobuilder.dat"
    content = {
        "Default Ruleset": {
            # Thermal part
            "t,fr,1,test thermal cluster": 4,
            "t,fr,1,other": 3,
            # Renewable part
            "r,fr,1,renewable cluster": 11,
            "r,fr,1,other": 12,
        }
    }
    IniWriter().write(content, file_path)

    # Remove the renewable
    area_fr.delete_renewable_cluster(area_fr.get_renewables()["renewable cluster"])
    # Checks the content -> 1 line should disappear
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "t,fr,1,test thermal cluster": 4,
            "t,fr,1,other": 3,
            "r,fr,1,other": 12,
        }
    }

    # Remove the thermal cluster
    area_fr.delete_thermal_cluster(area_fr.get_thermals()["test thermal cluster"])
    # Checks the content -> 1 line should disappear
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "t,fr,1,other": 3,
            "r,fr,1,other": 12,
        }
    }


def test_scenario_builder_sts_removals(local_study_93: Study) -> None:
    area_fr = local_study_93.get_areas()["fr"]
    # Create the necessary objects for the test
    sts = area_fr.create_st_storage("sts_test")
    sts.create_constraints([STStorageAdditionalConstraint(name="c1"), STStorageAdditionalConstraint(name="c2")])
    # Creates a scenario builder with thermal and renewable data
    file_path = Path(local_study_93.path) / "settings" / "scenariobuilder.dat"
    content = {
        "Default Ruleset": {
            # Short-term storage part
            "sts,fr,1,sts_test": 4,
            "sts,fr,1,other": 3,
            # Additional constraints part
            "sta,fr,1,sts_test,c1": 11,
            "sta,fr,1,sts_test,c2": 12,
            "sta,de,1,other,other": 13,
        }
    }
    IniWriter().write(content, file_path)

    # Remove the c1 constraint
    sts.delete_constraints(["c1"])
    # Checks the content -> 1 line should disappear
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "sts,fr,1,sts_test": 4,
            "sts,fr,1,other": 3,
            "sta,fr,1,sts_test,c2": 12,
            "sta,de,1,other,other": 13,
        }
    }

    # Remove the sts "sts_test"
    area_fr.delete_st_storage(storage=sts)
    # Checks the content -> 2 lines should disappear (we delete its constraints too)
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "sts,fr,1,other": 3,
            "sta,de,1,other,other": 13,
        }
    }


def test_scenario_builder_link_removals(local_study_w_links: Study) -> None:
    study = local_study_w_links
    file_path = Path(study.path) / "settings" / "scenariobuilder.dat"
    content = {
        "Default Ruleset": {
            "ntc,at,fr,1": 2,
            "ntc,at,fr,2": 3,
            "ntc,at,it,1": 4,
        }
    }
    IniWriter().write(content, file_path)

    # Remove the link
    study.delete_link(study.get_links()["at / fr"])

    # Check the content -> Only 1 line left
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "ntc,at,it,1": 4,
        }
    }


def test_scenario_builder_binding_constraints(local_study_w_constraints: Study) -> None:
    study = local_study_w_constraints
    file_path = Path(study.path) / "settings" / "scenariobuilder.dat"
    content = {
        "Default Ruleset": {
            "bc,default,1": 2,
            "bc,default,2": 3,
            "bc,group a,1": 4,
        }
    }
    IniWriter().write(content, file_path)

    # Remove the binding constraints
    study.delete_binding_constraints(list(study.get_binding_constraints().values()))

    # Check the content -> Only the group `group a` should still exist
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "bc,group a,1": 4,
        }
    }

    # Create a new constraint with group `group a`
    study.create_binding_constraint(name="bc_1", properties=BindingConstraintProperties(group="group a"))
    # Change the group of the constraint
    study.update_binding_constraints({"bc_1": BindingConstraintPropertiesUpdate(group="group b")})

    # Check the content -> Nothing left
    content = IniReader().read(file_path)
    assert content == {"Default Ruleset": {}}


def test_scenario_builder_area_removal(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    file_path = Path(study.path) / "settings" / "scenariobuilder.dat"
    content = {
        "Default Ruleset": {
            # Area `fr` related lines
            "ntc,at,fr,1": 2,
            "sts,fr,1,sts_test": 4,
            "sta,fr,1,sts_test,c2": 12,
            "t,fr,1,other": 3,
            "r,fr,1,other": 12,
            # Non-related lines
            "sta,de,1,other,other": 13,
            "bc,default,1": 2,
            "t,de,1,th1": 3,
            "r,de,1,renewable1": 12,
        }
    }
    IniWriter().write(content, file_path)

    # Remove the area
    study.delete_area(study.get_areas()["fr"])

    # Check the content -> Only 4 lines left
    content = IniReader().read(file_path)
    assert content == {
        "Default Ruleset": {
            "sta,de,1,other,other": 13,
            "bc,default,1": 2,
            "t,de,1,th1": 3,
            "r,de,1,renewable1": 12,
        }
    }
