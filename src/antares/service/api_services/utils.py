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


def get_matrix(url: str, wrapper: RequestWrapper) -> pd.DataFrame:
    response = wrapper.get(url)
    json_df = response.json()
    dataframe = pd.DataFrame(data=json_df["data"], index=json_df["index"], columns=json_df["columns"])
    return dataframe
