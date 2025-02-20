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
from dataclasses import asdict, dataclass
from enum import Enum
from typing import Any, Optional


class Solver(Enum):
    COIN = "coin"
    XPRESS = "xpress"
    SIRIUS = "sirius"


@dataclass
class AntaresSimulationParameters:
    solver: Solver = Solver.SIRIUS
    nb_cpu: Optional[int] = None
    unzip_output: bool = True
    output_suffix: Optional[str] = None
    presolve: bool = False

    @property
    def other_options(self) -> str:
        options = []
        if self.presolve:
            options.append("presolve")
        if self.solver != Solver.SIRIUS:
            options.append(self.solver.name)
        return " ".join(options)

    def to_api(self) -> dict[str, Any]:
        data = asdict(self)

        # Rename arg
        data["auto_unzip"] = data.pop("unzip_output")

        # Fill other options for the API model
        if self.other_options:
            data["other_options"] = self.other_options
        data.pop("solver", None)
        data.pop("presolve", None)

        # Removes optional options if not filled
        for key in ["nb_cpu", "output_suffix"]:
            if data[key] is None:
                data.pop(key)

        return data


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
