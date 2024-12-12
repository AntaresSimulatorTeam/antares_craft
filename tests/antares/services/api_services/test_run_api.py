import pytest
import requests_mock
import time
from unittest.mock import patch

from antares.api_conf.api_conf import APIconf
from antares.model.job import Job, JobStatus
from antares.model.settings.antares_simulation_parameters import AntaresSimulationParameters
from antares.model.settings.solver import Solver
from antares.model.study import Study
from antares.service.service_factory import ServiceFactory

def test_run_and_wait_antares_simulation():
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    study = Study("TestRunStudy", "880", ServiceFactory(api, study_id))
    parameters = AntaresSimulationParameters(Solver.SIRIUS, nb_cpu=2, unzip_output=True, presolve=False)

    with requests_mock.Mocker() as mocker:
        run_url = f"https://antares.com/api/v1/launcher/run/{study_id}"
        mocker.post(run_url, json="job_id", status_code=200)

        job_url = f"https://antares.com/api/v1/launcher/jobs/job_id"
        mocker.get(job_url, [
            {"json": {"job_id": "job_id", "status": "pending", "launcher_params": '{"auto_unzip": true}'}, "status_code": 200},
            {"json": {"job_id": "job_id", "status": "running", "launcher_params": '{"auto_unzip": true}'}, "status_code": 200},
            {"json": {"job_id": "job_id", "status": "success", "launcher_params": '{"auto_unzip": true}'}, "status_code": 200},
        ])

        tasks_url = "https://antares.com/api/v1/tasks"
        mocker.post(tasks_url, status_code=200)

        job = study.run_antares_simulation(parameters)
        assert isinstance(job, Job)
        assert job.job_id == "job_id"
        assert job.status == JobStatus.PENDING

        with patch("time.sleep", return_value=None):
            study.wait_job_completion(job, time_out=10)

        assert job.status == JobStatus.SUCCESS