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
import io
import time

import pandas as pd

from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import TaskFailedError, TaskTimeOutError

DEFAULT_TIME_OUT = 172800


def update_series(base_url: str, study_id: str, wrapper: RequestWrapper, series: pd.DataFrame, path: str) -> None:
    url = f"{base_url}/studies/{study_id}/raw?path={path}"
    array_data = series.to_numpy().tolist()
    wrapper.post(url, json=array_data)


def get_matrix(base_url: str, study_id: str, wrapper: RequestWrapper, series_path: str) -> pd.DataFrame:
    raw_url = f"{base_url}/studies/{study_id}/raw?path={series_path}&matrix_format=arrow compressed"
    response = wrapper.get(raw_url)
    return pd.read_feather(io.BytesIO(response.content))


def wait_task_completion(
    base_url: str, wrapper: RequestWrapper, task_id: str, repeat_interval: int = 2, time_out: int = DEFAULT_TIME_OUT
) -> None:
    url = f"{base_url}/tasks/{task_id}"

    start_time = time.time()
    task_result = None

    while not task_result:
        if time.time() - start_time > time_out:
            raise TaskTimeOutError(task_id, time_out)
        response = wrapper.get(url)
        task = response.json()
        task_result = task["result"]
        time.sleep(repeat_interval)

    if not task_result["success"]:
        raise TaskFailedError(task_id)
