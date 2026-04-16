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

import numpy as np
import pandas as pd

from antares.craft import (
    AdequacyPatchMode,
    AreaProperties,
    AreaUi,
    AssetType,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BuildingMode,
    ConstraintTerm,
    FilterOption,
    GeneralParametersUpdate,
    HydroPropertiesUpdate,
    LinkData,
    LinkProperties,
    LinkStyle,
    LinkUi,
    Occurrence,
    RenewableClusterProperties,
    STStorageAdditionalConstraint,
    STStorageGroup,
    STStorageProperties,
    Study,
    StudySettingsUpdate,
    ThermalClusterProperties,
    create_study_local,
    read_study_local,
)
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError, OutputDataRetrievalError
from antares.craft.model.commons import STUDY_VERSION_8_8, STUDY_VERSION_9_3
from antares.craft.model.simulation import AntaresSimulationParametersLocal, JobStatus
from antares.study.version import StudyVersion


def find_executable_path(version: str) -> Path:
    solver_parent_path = (
        [p for p in Path(__file__).parents if p.name == "antares_craft"][0]
        / "AntaresWebDesktop"
        / "AntaresWeb"
        / "antares_solver"
        / version
    )
    return list(solver_parent_path.glob("antares-*"))[0]


def _set_up_real_case_study(path: Path, version: StudyVersion) -> Study:
    study = create_study_local("test study", str(version), path)

    # Create 2 areas
    area_fr_properties = AreaProperties(
        adequacy_patch_mode=AdequacyPatchMode.INSIDE, energy_cost_spilled=42, filter_synthesis={FilterOption.DAILY}
    )
    area_fr_ui = AreaUi(x=27, color_rgb=[43, 27, 61])
    area_fr = study.create_area("FR", properties=area_fr_properties, ui=area_fr_ui)
    # needed for the simulation to succeed
    area_fr.hydro.update_properties(HydroPropertiesUpdate(reservoir_capacity=1))

    area_be_properties = AreaProperties(
        other_dispatch_power=False,
        energy_cost_unsupplied=1000,
        filter_by_year={FilterOption.MONTHLY, FilterOption.ANNUAL},
    )
    area_be_ui = AreaUi(y=4)
    area_be = study.create_area("be", properties=area_be_properties, ui=area_be_ui)
    area_be.hydro.update_properties(HydroPropertiesUpdate(reservoir_capacity=1))

    # Create a link
    link_properties = LinkProperties(asset_type=AssetType.DC, display_comments=False)
    link_ui = LinkUi(link_style=LinkStyle.DOT, colorr=3)
    study.create_link(area_from=area_fr.id, area_to=area_be.id, properties=link_properties, ui=link_ui)

    # Create thermal cluster
    th_properties = ThermalClusterProperties(group="nuclear", unit_count=12, nominal_capacity=43)
    area_fr.create_thermal_cluster("Nuclear_fr", th_properties)

    # Create renewable cluster
    renewable_properties = RenewableClusterProperties(group="wind onshore", enabled=False)
    area_fr.create_renewable_cluster("Wind onshore fr", renewable_properties)

    # Create short term storage
    sts_properties = STStorageProperties(group=STStorageGroup.BATTERY.value, efficiency=0.4)
    area_fr.create_st_storage("Battery fr", sts_properties)

    # Create binding constraint
    term = ConstraintTerm(weight=12, offset=3, data=LinkData(area_be.id, area_fr.id))
    bc_properties = BindingConstraintProperties(
        group="my_group", operator=BindingConstraintOperator.LESS, time_step=BindingConstraintFrequency.WEEKLY
    )
    study.create_binding_constraint(name="BC_1", properties=bc_properties, terms=[term])

    # Set up scenario builder and use it
    sc_builder = study.get_scenario_builder()
    sc_builder.load.get_area("fr").set_new_scenario([2, 1, None])
    study.set_scenario_builder(sc_builder)
    study.get_areas()["fr"].set_load(pd.DataFrame(np.zeros((8760, 4))))  # Add columns for the ScBuilder for find them.

    new_parameters = StudySettingsUpdate(
        general_parameters=GeneralParametersUpdate(building_mode=BuildingMode.CUSTOM, nb_years=3)
    )
    study.update_settings(new_parameters)

    return study


class TestLocalLauncher:
    def test_error_case(self, tmp_path: Path) -> None:
        study = create_study_local("test study", "880", tmp_path)
        # Ensure it's impossible to run a study without giving a solver path inside the parameters
        with pytest.raises(
            AntaresSimulationRunningError,
            match=re.escape("Could not run the simulation for study 'test study': No solver path was provided"),
        ):
            study.run_antares_simulation()

        study = read_study_local(tmp_path / "test study")

        # Asserts running a simulation without areas fail and doesn't create an output file
        solver_path = find_executable_path("8_8")
        default_parameters = AntaresSimulationParametersLocal(solver_path=solver_path)
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.FAILED
        assert job.parameters == default_parameters
        assert job.output_id is None
        output_path = Path(study.path / "output")
        assert list(output_path.iterdir()) == []

    def test_lifecycle(self, tmp_path: Path) -> None:
        solver_path = find_executable_path("8_8")
        study = create_study_local("test study", "880", tmp_path)
        output_path = Path(study.path / "output")

        # Simulation succeeds
        study.create_area("area_1")
        default_parameters = AntaresSimulationParametersLocal(solver_path=solver_path)
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS
        assert job.parameters == default_parameters
        outputs = list(output_path.iterdir())
        assert len(outputs) == 1
        output_id = outputs[0].name
        assert job.output_id == output_id
        assert not output_id.endswith(".zip")
        # Ensures the `get_outputs` method returns the generated output
        study_outputs = study.get_outputs()
        assert len(study_outputs) == 1
        assert list(study_outputs.keys())[0] == output_id

        # Runs simulation with parameters
        simulation_parameters = AntaresSimulationParametersLocal(
            solver_path=solver_path, unzip_output=False, output_suffix="test_integration"
        )
        second_job = study.run_antares_simulation(simulation_parameters)
        study.wait_job_completion(second_job)
        assert second_job.status == JobStatus.SUCCESS
        assert second_job.parameters == simulation_parameters
        outputs = list(output_path.iterdir())
        assert len(outputs) == 2
        second_output = [otp.name for otp in outputs if otp.name.endswith(".zip")][0]
        assert second_job.output_id == second_output
        assert second_output.endswith(".zip")

        # Runs a third simulation just for the rest of the test
        third_job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(third_job)
        assert third_job.status == JobStatus.SUCCESS
        outputs = list(output_path.iterdir())
        assert len(outputs) == 3
        expected_outputs = sorted([output.name for output in outputs])

        # Asserts read_outputs return the expected result
        study._read_outputs()
        assert sorted(list(study.get_outputs().keys())) == expected_outputs

        # Asserts read_study_local reads the outputs
        second_study = read_study_local(tmp_path / "test study")
        assert sorted(list((second_study.get_outputs()).keys())) == expected_outputs

        # Deletes the first output
        study.delete_output(output_id)
        outputs = list(output_path.iterdir())
        assert len(outputs) == 2
        assert len(study.get_outputs()) == 2

        # Deletes all outputs
        study.delete_outputs()
        outputs = list(output_path.iterdir())
        assert len(outputs) == 0
        assert study.get_outputs() == {}

    def test_version_92(self, tmp_path: Path) -> None:
        solver_path = find_executable_path("9_2")
        default_parameters = AntaresSimulationParametersLocal(solver_path=solver_path)
        study = create_study_local("test study", "920", tmp_path)

        # Simulation succeeds
        study.create_area("area_1")
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS

    def test_simulation_succeeds_with_real_study(self, tmp_path: Path) -> None:
        solver_path = find_executable_path("8_8")
        study = _set_up_real_case_study(tmp_path, STUDY_VERSION_8_8)
        # Run the simulation
        default_parameters = AntaresSimulationParametersLocal(solver_path=solver_path)
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS

    def test_ts_numbers(self, tmp_path: Path) -> None:
        solver_path = find_executable_path("9_3")
        study = _set_up_real_case_study(tmp_path, STUDY_VERSION_9_3)

        # Create a short-term storage constraint
        study.get_areas()["fr"].get_st_storages()["battery fr"].create_constraints(
            [STStorageAdditionalConstraint(name="c1", occurrences=[Occurrence(hours=[1, 2])])]
        )

        # Use `store_new_set` to generate `ts-numbers` files
        new_params = GeneralParametersUpdate(store_new_set=True)
        study.update_settings(StudySettingsUpdate(general_parameters=new_params))

        # Run the Simulation
        default_parameters = AntaresSimulationParametersLocal(solver_path=solver_path)
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS

        output = next(iter(study.get_outputs().values()))

        # Check the ts-numbers
        default_values = {1: 1, 2: 1, 3: 1}
        assert output.get_solar_ts_numbers("fr") == default_values
        assert output.get_load_ts_numbers("fr") == {1: 2, 2: 1, 3: 2}  # Not default values as we set them
        assert output.get_wind_ts_numbers("fr") == default_values
        assert output.get_hydro_ts_numbers("fr") == default_values
        assert output.get_link_ts_numbers("be", "fr") == default_values
        assert output.get_binding_constraint_ts_numbers("my_group") == default_values
        assert output.get_thermal_ts_numbers("fr", "nuclear_fr") == default_values
        assert output.get_st_storage_inflows_numbers("fr", "battery fr") == default_values
        assert output.get_st_storage_additional_constraints_numbers("fr", "battery fr", "c1") == default_values

        # Ask for a fake area
        with pytest.raises(OutputDataRetrievalError):
            output.get_solar_ts_numbers("fake_area")

        study.delete_outputs()

        # Set `store_new_set` to False to not have the `ts-numbers` folder and check the issue
        new_params = GeneralParametersUpdate(store_new_set=False)
        study.update_settings(StudySettingsUpdate(general_parameters=new_params))
        job = study.run_antares_simulation(default_parameters)
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS

        output = next(iter(study.get_outputs().values()))
        with pytest.raises(OutputDataRetrievalError, match="The `ts-numbers` folder does not exist"):
            output.get_solar_ts_numbers("fr")
