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

from typing import Optional

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import (
    AntaresSimulationRunningError,
    AntaresSimulationUnzipError,
    APIError,
    SimulationTimeOutError,
)
from antares.model.job import Job, JobStatus
from antares.model.settings.antares_simulation_parameters import AntaresSimulationParameters
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
                payload = parameters.to_json()
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
        launcher_params = json.loads(job_info["launcher_params"])
        return Job(job_id, job_info["status"], launcher_params["auto_unzip"])

    def wait_job_completion(self, job: Job, time_out: int) -> None:
        start_time = time.time()
        repeat_interval = 5
        while job.status in (JobStatus.RUNNING, JobStatus.PENDING):
            if time.time() - start_time > time_out:
                raise SimulationTimeOutError(job.job_id, time_out)
            time.sleep(repeat_interval)
            updated_job = self._get_job_from_id(job.job_id)
            job.status = updated_job.status
            job.unzip_output = updated_job.unzip_output

        if job.unzip_output:
            self._unzip_output(self.study_id, ["UNARCHIVE"])

        return None

    def _unzip_output(self, ref_id: str, type: list[str]) -> None:
        url = f"{self._base_url}/tasks"
        try:
            payload = {
                "status": [],
                "name": "string",
                "type": type,
                "ref_id": ref_id,
                "from_creation_date_utc": 0,
                "to_creation_date_utc": 0,
                "from_completion_date_utc": 0,
                "to_completion_date_utc": 0,
            }
            self._wrapper.post(url, json=payload)
        except APIError as e:
            raise AntaresSimulationUnzipError(self.study_id, e.message) from e
