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
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Optional


class Solver(Enum):
    """Name of possible solvers.
    
    Attributes:
        COIN: [Coin](https://github.com/coin-or/Clp) solver .
        XPRESS: [FICO(r) Xpress Optimization](https://www.fico.com/en/products/fico-xpress-optimization) solver.
        SIRIUS: [Sirius](https://github.com/AntaresSimulatorTeam/sirius-solver) solver, RTE original solver.
    """
    COIN = "coin"
    XPRESS = "xpress"
    SIRIUS = "sirius"


@dataclass
class AntaresSimulationParametersAPI:
    """Antares simulation parameters when launching via the API. 

    Attributes:
        solver: Solver name.
        solver_version: Solver version.
        nb_cpu: Number of CPU needed for the simulation.
        unzip_output: Whether to automatically unzip the output folder of the simulator.
        output_suffix: Output suffix to append to the name composed by default by the time-stamp of the launch.
        launcher: HPC cluster name.
        preset: Low level parameter preset name for simulation acceleration.
        other_options: Other options for R&D testing and optimizations 
            corresponding to a mapping of the CLI arguments for the solver executable.
    """
    solver: Optional[Solver] = None
    solver_version: Optional[str] = None
    nb_cpu: Optional[int] = None
    unzip_output: bool = True
    output_suffix: Optional[str] = None
    launcher: Optional[str] = None
    preset: Optional[str] = None
    other_options: Optional[str] = None


@dataclass
class AntaresSimulationParametersLocal:
    """Antares simulation parameters when launching a simulation locally.

    Attributes:
        solver_path: Path to the solver on the computer.
        solver: Name of the solver.
        nb_cpu: Number of CPU needed for the simulation.
        unzip_output: Whether to automatically unzip the output folder of the simulator.
        output_suffix: Output suffix to append to the name composed by default by the time-stamp of the launch.
    """
    solver_path: Path
    solver: Solver = Solver.SIRIUS
    nb_cpu: Optional[int] = None
    unzip_output: bool = True
    output_suffix: Optional[str] = None


AntaresSimulationParameters = AntaresSimulationParametersLocal | AntaresSimulationParametersAPI


class JobStatus(Enum):
    """Status of the simulation.
    
    Attributes:
        PENDING:
        RUNNING:
        SUCCESS:
        FAILED:
    """
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    @staticmethod
    def from_str(input: str) -> "JobStatus":
        return JobStatus.__getitem__(input.upper())


@dataclass
class Job:
    """Job for the the simulation.
    
    Attributes:
        job_id: Job ID.
        status: Job status (pending, running, success or failed.)
        parameters: Local or API parameters.
        output_id: Output ID.
    """
    job_id: str
    status: JobStatus
    parameters: AntaresSimulationParameters
    output_id: Optional[str] = None
