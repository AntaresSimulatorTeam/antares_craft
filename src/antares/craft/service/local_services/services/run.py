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
import subprocess

from pathlib import Path
from typing import Any, Optional

import psutil

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError, SimulationTimeOutError
from antares.craft.model.simulation import AntaresSimulationParameters, Job, JobStatus
from antares.craft.service.base_services import BaseRunService
from antares.study.version import SolverVersion
from typing_extensions import override


def _get_solver_version(solver_path: Path) -> SolverVersion:
    solver_name = solver_path.name
    solver_version_str = solver_name.removeprefix("antares-").removesuffix("-solver")
    return SolverVersion.parse(solver_version_str)


class RunLocalService(BaseRunService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def run_antares_simulation(
        self, parameters: Optional[AntaresSimulationParameters] = None, solver_path: Optional[Path] = None
    ) -> Job:
        if not solver_path:
            raise AntaresSimulationRunningError(self.study_name, "No solver path was provided")
        args = [str(solver_path)]
        if parameters:
            solver_version = _get_solver_version(solver_path)
            args += parameters.to_local(solver_version)
        args.append(str(self.config.study_path))

        parameters = parameters or AntaresSimulationParameters()
        process = subprocess.Popen(args, universal_newlines=True, encoding="utf-8")
        return Job(job_id=str(process.pid), status=JobStatus.RUNNING, parameters=parameters, output_id=None)

    @override
    def wait_job_completion(self, job: Job, time_out: int) -> None:
        pid = int(job.job_id)
        try:
            process = psutil.Process(pid)

            return_code = process.wait(timeout=time_out)
            if return_code == 0:
                self._handle_success(job)
            else:
                self._handle_failure(job)

        except psutil.NoSuchProcess:
            return self._handle_simulation_ending()
        except psutil.TimeoutExpired:
            raise SimulationTimeOutError(job.job_id, time_out)

    def _handle_simulation_ending(self):
        pass
        # todo: we should find what happened

    def _handle_success(self, job: Job):
        job.status = JobStatus.SUCCESS
        # todo: we should find the job.output_id

    def _handle_failure(self, job: Job):
        job.status = JobStatus.FAILED
        # todo: we should find the job.output_id

    def _find_output_id(self, job: Job) -> str:
        output_path = self.config.study_path / "output"
        all_outputs = output_path.iterdir()
        zipped_outputs = []
        unzipped_outputs = []
        for output in all_outputs:
            if output.name.endswith(".zip"):
                zipped_outputs.append(output)
            else:
                unzipped_outputs.append(output)

        if job.parameters.unzip_output:
            # todo: look inside unzipped_outputs
        else:
            # todo: look inside zipped_outputs