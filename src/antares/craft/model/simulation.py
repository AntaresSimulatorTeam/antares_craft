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
    COIN = "coin"
    XPRESS = "xpress"
    SIRIUS = "sirius"


@dataclass
class XpansionSimulationMode:
    classic: bool = True
    sensitivity: bool = False
    adequacy_criterion: bool = False


@dataclass
class AntaresSimulationParametersAPI:
    solver: Solver = Solver.SIRIUS
    solver_version: Optional[str] = None
    nb_cpu: Optional[int] = None
    unzip_output: bool = True
    output_suffix: Optional[str] = None
    launcher: Optional[str] = None
    preset: Optional[str] = None
    xpansion: Optional[XpansionSimulationMode] = None
    other_options: Optional[str] = None


@dataclass
class AntaresSimulationParametersLocal:
    solver_path: Path
    solver: Solver = Solver.SIRIUS
    nb_cpu: Optional[int] = None
    unzip_output: bool = True
    output_suffix: Optional[str] = None


AntaresSimulationParameters = AntaresSimulationParametersLocal | AntaresSimulationParametersAPI


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    @staticmethod
    def from_str(input: str) -> "JobStatus":
        return JobStatus.__getitem__(input.upper())


@dataclass
class Job:
    job_id: str
    status: JobStatus
    parameters: AntaresSimulationParameters
    output_id: Optional[str] = None
