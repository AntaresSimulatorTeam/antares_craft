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

import pandas as pd

from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import APIError, MatrixUploadError
from antares.model.area import Area


def _upload_series(
    base_url: str, study_id: str, wrapper: RequestWrapper, series: pd.DataFrame, path: str, matrix_type: str, area: Area
) -> None:
    try:
        url = f"{base_url}/studies/{study_id}/raw?path={path}"
        array_data = series.to_numpy().tolist()
        wrapper.post(url, json=array_data)
    except APIError as e:
        raise MatrixUploadError(area.id, matrix_type, e.message) from e


def get_matrix(
    base_url: str, study_id: str, wrapper: RequestWrapper, series_path: str, matrix_type: str
) -> pd.DataFrame:
    raw_url = f"{base_url}/studies/{study_id}/raw?path={series_path}"
    response = wrapper.get(raw_url)
    json_df = response.json()
    dataframe = pd.DataFrame(data=json_df["data"], index=json_df["index"], columns=json_df["columns"])
    return dataframe
