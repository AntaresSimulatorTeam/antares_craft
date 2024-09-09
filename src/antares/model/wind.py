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
from pathlib import Path
from typing import Optional

import pandas as pd

from antares.tools.prepro_folder import PreproFolder
from antares.tools.time_series_tool import TimeSeries, TimeSeriesFile


class Wind:
    def __init__(
        self,
        time_series: pd.DataFrame = pd.DataFrame([]),
        local_file: Optional[TimeSeriesFile] = None,
        study_path: Optional[Path] = None,
        area_id: Optional[str] = None,
    ) -> None:
        self._time_series = TimeSeries(time_series, local_file)
        self._prepro = (
            PreproFolder(folder="wind", study_path=study_path, area_id=area_id) if study_path and area_id else None
        )

    @property
    def time_series(self) -> TimeSeries:
        return self._time_series

    @property
    def prepro(self) -> Optional[PreproFolder]:
        return self._prepro
