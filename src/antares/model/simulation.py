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

from enum import Enum
from typing import Any, Optional

from pydantic import BaseModel, Field


class Solver(Enum):
    COIN = "coin"
    XPRESS = "xpress"
    SIRIUS = "sirius"


class AntaresSimulationParameters(BaseModel):
    solver: Solver = Solver.SIRIUS
    nb_cpu: Optional[int] = None
    unzip_output: bool = Field(alias="auto_unzip", default=True)
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
        data = self.model_dump(by_alias=True)
        if self.other_options:
            data["other_options"] = self.other_options
        data.pop("solver", None)
        data.pop("presolve", None)
        return data


class JobStatus(Enum):
    PENDING = "pending"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"

    @staticmethod
    def from_str(input: str) -> "JobStatus":
        return JobStatus.__getitem__(input.upper())


class Job(BaseModel):
    job_id: str
    status: JobStatus
    output_id: Optional[str] = None
    parameters: AntaresSimulationParameters
