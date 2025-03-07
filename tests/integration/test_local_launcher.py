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

from antares.craft import create_study_local, read_study_local
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError
from antares.craft.model.hydro import HydroPropertiesUpdate
from antares.craft.model.simulation import AntaresSimulationParameters, JobStatus


def find_executable_path() -> Path:
    solver_parent_path = (
        [p for p in Path(__file__).parents if p.name == "antares_craft"][0]
        / "AntaresWebDesktop"
        / "AntaresWeb"
        / "antares_solver"
    )
    return list(solver_parent_path.glob("antares-*"))[0]


class TestLocalLauncher:
    def test_error_case(self, tmp_path: Path):
        study = create_study_local("test study", "880", tmp_path)
        # Ensure it's impossible to run a study without giving a solver path at the instantiation
        with pytest.raises(
            AntaresSimulationRunningError,
            match=re.escape("Could not run the simulation for study test study: No solver path was provided"),
        ):
            study.run_antares_simulation()

        solver_path = find_executable_path()
        study = read_study_local(tmp_path / "test study", solver_path)

        # Asserts running a simulation without areas fail and doesn't create an output file
        job = study.run_antares_simulation()
        study.wait_job_completion(job)
        assert job.status == JobStatus.FAILED
        assert job.parameters == AntaresSimulationParameters()
        assert job.output_id is None
        output_path = Path(study.path / "output")
        assert list(output_path.iterdir()) == []

    def test_lifecycle(self, tmp_path: Path):
        solver_path = find_executable_path()
        study = create_study_local("test study", "880", tmp_path, solver_path)
        output_path = Path(study.path / "output")

        # Simulation succeeds
        area_1 = study.create_area("area_1")
        area_1.hydro.update_properties(HydroPropertiesUpdate(reservoir_capacity=1))  # make the simulation succeeds
        job = study.run_antares_simulation()
        study.wait_job_completion(job)
        assert job.status == JobStatus.SUCCESS
        assert job.parameters == AntaresSimulationParameters()
        outputs = list(output_path.iterdir())
        assert len(outputs) == 1
        output_id = outputs[0].name
        assert job.output_id == output_id
        assert not output_id.endswith(".zip")

        # Runs simulation with parameters
        simulation_parameters = AntaresSimulationParameters(unzip_output=False, output_suffix="test_integration")
        second_job = study.run_antares_simulation(simulation_parameters)
        study.wait_job_completion(second_job)
        assert second_job.status == JobStatus.SUCCESS
        assert second_job.parameters == simulation_parameters
        outputs = list(output_path.iterdir())
        assert len(outputs) == 2
        second_output = [otp.name for otp in outputs if otp.name.endswith(".zip")][0]
        assert second_job.output_id == second_output
        assert second_output.endswith(".zip")
