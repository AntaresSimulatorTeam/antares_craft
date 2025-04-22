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
import shutil
import subprocess

from datetime import datetime
from pathlib import Path
from typing import Any, Optional

import psutil

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError, SimulationTimeOutError
from antares.craft.model.simulation import AntaresSimulationParameters, Job, JobStatus
from antares.craft.service.base_services import BaseRunService
from antares.study.version import SolverVersion


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

        # Builds command line call
        args = [str(solver_path)]
        parameters = parameters or AntaresSimulationParameters()
        solver_version = _get_solver_version(solver_path)
        args += parameters.to_local(solver_version)
        args += ["-i", str(self.config.study_path)]

        # Launches the simulation
        process = subprocess.Popen(
            args, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, universal_newlines=True, encoding="utf-8"
        )

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
            return self._handle_simulation_ending(job)
        except psutil.TimeoutExpired:
            raise SimulationTimeOutError(job.job_id, time_out)

    def _handle_simulation_ending(self, job: Job) -> None:
        output_id = self._find_most_recent_output(job.parameters.unzip_output)
        if output_id.endswith(".zip"):
            job.status = JobStatus.SUCCESS
            job.output_id = output_id
        else:
            output_path = self.config.study_path / "output" / output_id
            if (output_path / "execution_info.ini").exists():
                job.status = JobStatus.SUCCESS
                job.output_id = output_id
            else:
                job.status = JobStatus.FAILED
                shutil.rmtree(output_path)

    def _handle_success(self, job: Job) -> None:
        job.status = JobStatus.SUCCESS
        job.output_id = self._find_most_recent_output(job.parameters.unzip_output)

    def _handle_failure(self, job: Job) -> None:
        job.status = JobStatus.FAILED
        output_id = self._find_most_recent_output(job.parameters.unzip_output)
        shutil.rmtree(self.config.study_path / "output" / output_id)

    def _find_most_recent_output(self, output_is_unzipped: bool) -> str:
        output_path = self.config.study_path / "output"
        all_outputs = output_path.iterdir()
        zipped_outputs = []
        unzipped_outputs = []
        for output in all_outputs:
            if output.name.endswith(".zip"):
                zipped_outputs.append(output.name)
            else:
                unzipped_outputs.append(output.name)

        end_of_date_pattern = 13
        concerned_list = unzipped_outputs if output_is_unzipped else zipped_outputs
        output_result_tuple: tuple[float, str] = (0, "")
        for output_name in concerned_list:
            output_date_as_str = output_name[:end_of_date_pattern]
            output_date_as_datetime = datetime.strptime(output_date_as_str, "%Y%m%d-%H%M")
            total_seconds = output_date_as_datetime.timestamp()
            if total_seconds > output_result_tuple[0]:
                output_result_tuple = (total_seconds, output_name)
        return output_result_tuple[1]
