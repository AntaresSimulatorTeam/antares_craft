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
import time

from pathlib import Path
from typing import Any, Optional, cast

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    AntaresSimulationRunningError,
    AntaresSimulationUnzipError,
    APIError,
    SimulationFailedError,
    SimulationTimeOutError,
    TaskFailedError,
)
from antares.craft.model.simulation import AntaresSimulationParameters, Job, JobStatus
from antares.craft.service.api_services.utils import wait_task_completion
from antares.craft.service.base_services import BaseRunService


class RunApiService(BaseRunService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def run_antares_simulation(
        self, parameters: Optional[AntaresSimulationParameters] = None, solver_path: Optional[Path] = None
    ) -> Job:
        url = f"{self._base_url}/launcher/run/{self.study_id}"
        try:
            if parameters is not None:
                payload = parameters.to_api()
                response = self._wrapper.post(url, json=payload)
            else:
                parameters = AntaresSimulationParameters()
                response = self._wrapper.post(url)
            job_id = response.json()["job_id"]
            return self._get_job_from_id(job_id, parameters)
        except APIError as e:
            raise AntaresSimulationRunningError(self.study_id, e.message) from e

    def _get_job_from_id(self, job_id: str, parameters: AntaresSimulationParameters) -> Job:
        url = f"{self._base_url}/launcher/jobs/{job_id}"
        response = self._wrapper.get(url)
        job_info = response.json()
        status = JobStatus.from_str(job_info["status"])
        output_id = job_info.get("output_id")
        return Job(job_id=job_id, status=status, parameters=parameters, output_id=output_id)

    @override
    def wait_job_completion(self, job: Job, time_out: int) -> None:
        start_time = time.time()
        repeat_interval = 5
        if job.status == JobStatus.SUCCESS:
            self._update_job(job)

        while job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            if time.time() - start_time > time_out:
                raise SimulationTimeOutError(job.job_id, time_out)
            time.sleep(repeat_interval)
            self._update_job(job)

        if job.status == JobStatus.FAILED or not job.output_id:
            raise SimulationFailedError(self.study_id, job.job_id)

        if job.parameters.unzip_output:
            try:
                self._wait_unzip_output(self.study_id, job, time_out)
            except AntaresSimulationUnzipError as e:
                raise SimulationFailedError(self.study_id, job.job_id) from e

        return None

    def _update_job(self, job: Job) -> None:
        updated_job = self._get_job_from_id(job.job_id, job.parameters)
        job.status = updated_job.status
        job.output_id = updated_job.output_id

    def _wait_unzip_output(self, ref_id: str, job: Job, time_out: int) -> None:
        url = f"{self._base_url}/tasks"
        repeat_interval = 2
        payload = {"type": ["UNARCHIVE"], "ref_id": ref_id}
        try:
            response = self._wrapper.post(url, json=payload)
            tasks = response.json()
            task_id = self._get_unarchiving_task_id(job, tasks)
            wait_task_completion(self._base_url, self._wrapper, task_id, repeat_interval, time_out)
        except (APIError, TaskFailedError) as e:
            raise AntaresSimulationUnzipError(self.study_id, job.job_id, e.message) from e

    def _get_unarchiving_task_id(self, job: Job, tasks: list[dict[str, Any]]) -> str:
        for task in tasks:
            task_name = task["name"]
            output_id = task_name.split("/")[-1].split(" ")[0]
            if output_id == job.output_id:
                return cast(str, task["id"])
        raise AntaresSimulationUnzipError(self.study_id, job.job_id, "Could not find task for unarchiving job")
