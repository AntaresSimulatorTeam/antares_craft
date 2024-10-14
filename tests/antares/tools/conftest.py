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

import numpy as np
import pandas as pd
import pytest

from antares.tools.time_series_tool import TimeSeriesFile, TimeSeriesFileType


@pytest.fixture
def time_series_data():
    return pd.DataFrame(np.zeros([2, 3]))


@pytest.fixture
def time_series_file(tmp_path, time_series_data):
    return TimeSeriesFile(TimeSeriesFileType.RESERVES, tmp_path, area_id="test", time_series=time_series_data)
