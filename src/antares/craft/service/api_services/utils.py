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

from antares.craft.api_conf.request_wrapper import RequestWrapper


def upload_series(base_url: str, study_id: str, wrapper: RequestWrapper, series: pd.DataFrame, path: str) -> None:
    url = f"{base_url}/studies/{study_id}/raw?path={path}"
    array_data = series.to_numpy().tolist()
    wrapper.post(url, json=array_data)


def get_matrix(base_url: str, study_id: str, wrapper: RequestWrapper, series_path: str) -> pd.DataFrame:
    raw_url = f"{base_url}/studies/{study_id}/raw?path={series_path}"
    response = wrapper.get(raw_url)
    json_df = response.json()

    if "index" in json_df:
        dataframe = pd.DataFrame(data=json_df["data"], index=json_df["index"], columns=json_df["columns"])
    else:
        dataframe = pd.DataFrame(data=json_df["data"], columns=json_df["columns"])
    return dataframe
