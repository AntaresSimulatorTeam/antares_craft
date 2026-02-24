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

from antares.craft.model.simulation import AntaresSimulationParametersLocal, Solver
from antares.craft.service.local_services.services.run import convert_parameters_to_command_line
from antares.study.version import SolverVersion


def test_convert_parameters_to_command_line_for_local() -> None:
    solver_path = Path("tmp")
    default_solver_version = SolverVersion.parse("9.3")
    # Default parameters
    params = AntaresSimulationParametersLocal(solver_path=solver_path)
    assert convert_parameters_to_command_line(params, default_solver_version) == ["tmp", "--solver=sirius"]

    # Use the other solvers
    for solver in [Solver.COIN, Solver.XPRESS]:
        params = AntaresSimulationParametersLocal(solver_path=solver_path, solver=solver)
        assert convert_parameters_to_command_line(params, default_solver_version) == ["tmp", f"--solver={solver.value}"]

    # Asks for a certain number of CPUs
    params = AntaresSimulationParametersLocal(solver_path=solver_path, nb_cpu=12)
    assert convert_parameters_to_command_line(params, default_solver_version) == [
        "tmp",
        "--force-parallel",
        "12",
        "--solver=sirius",
    ]

    # Asks for the output to be unzipped
    params = AntaresSimulationParametersLocal(solver_path=solver_path, unzip_output=False)
    assert convert_parameters_to_command_line(params, default_solver_version) == ["tmp", "-z", "--solver=sirius"]

    # Asks for a suffix for the output
    params = AntaresSimulationParametersLocal(solver_path=solver_path, output_suffix="my_suffix")
    assert convert_parameters_to_command_line(params, default_solver_version) == [
        "tmp",
        "-n",
        "my_suffix",
        "--solver=sirius",
    ]

    # Asks for solver for an older solver version
    old_solver_version = SolverVersion.parse("8.8")
    for solver in [Solver.COIN, Solver.XPRESS, Solver.SIRIUS]:
        params = AntaresSimulationParametersLocal(solver_path=solver_path, solver=solver)
        result = convert_parameters_to_command_line(params, old_solver_version)
        if solver == Solver.SIRIUS:
            assert result == ["tmp"]
        else:
            assert result == ["tmp", "--use-ortools", " --ortools-solver", solver.value]
