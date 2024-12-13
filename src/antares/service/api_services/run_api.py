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
import json
import time

from typing import Any, Optional

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import (
    AntaresSimulationRunningError,
    AntaresSimulationUnzipError,
    APIError,
    SimulationFailedError,
    SimulationTimeOutError,
)
from antares.model.simulation import AntaresSimulationParameters, Job, JobStatus
from antares.service.base_services import BaseRunService


class RunApiService(BaseRunService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    def run_antares_simulation(self, parameters: Optional[AntaresSimulationParameters] = None) -> Job:
        url = f"{self._base_url}/launcher/run/{self.study_id}"
        try:
            if parameters is not None:
                payload = parameters.to_api()
                response = self._wrapper.post(url, json=payload)
            else:
                response = self._wrapper.post(url)
            job_id = response.json()["id"]
            return self._get_job_from_id(job_id)
        except APIError as e:
            raise AntaresSimulationRunningError(self.study_id, e.message) from e

    def _get_job_from_id(self, job_id: str) -> Job:
        url = f"{self._base_url}/launcher/jobs/{job_id}"
        response = self._wrapper.get(url)
        job_info = response.json()
        status = JobStatus.from_str(job_info["status"])
        output_id = job_info["output_id"] if status == JobStatus.SUCCESS else None
        launcher_params = json.loads(job_info["launcher_params"])
        return Job(job_id=job_id, status=status, unzip_output=launcher_params["auto_unzip"], output_id=output_id)

    def wait_job_completion(self, job: Job, time_out: int) -> None:
        start_time = time.time()
        repeat_interval = 5
        while job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            if time.time() - start_time > time_out:
                raise SimulationTimeOutError(job.job_id, time_out)
            time.sleep(repeat_interval)
            updated_job = self._get_job_from_id(job.job_id)
            job.status = updated_job.status
            job.output_id = updated_job.output_id

        if job.status == JobStatus.FAILED:
            raise SimulationFailedError(self.study_id)

        if job.unzip_output:
            self._wait_unzip_output(self.study_id, ["UNARCHIVE"], job.output_id)

        return None

    def _wait_unzip_output(self, ref_id: str, type: list[str], job_output_id: str) -> None:
        url = f"{self._base_url}/tasks"
        repeat_interval = 2
        payload = {"type": type, "ref_id": ref_id}
        try:
            response = self._wrapper.post(url, json=payload)
            tasks = response.json()
            task_id = self._get_task_id(job_output_id, tasks)
            url += f"/{task_id}"
            self._get_task_until_success(url, repeat_interval)
        except APIError as e:
            raise AntaresSimulationUnzipError(self.study_id, e.message) from e

    def _get_task_id(self, job_output_id: str, tasks: list[dict[str, Any]]) -> str:
        for task in tasks:
            task_name = task["name"]
            output_id = task_name.split("/")[-1].split(" ")[0]
            if output_id == job_output_id:
                return task["id"]

    def _get_task_until_success(self, url: str, repeat_interval: int) -> None:
        task_success = False
        while not task_success:
            response = self._wrapper.get(url)
            task = response.json()
            task_success = task["result"]["success"]
            time.sleep(repeat_interval)
