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
from enum import Enum
from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft.tools.matrix_tool import write_timeseries
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class PreproFolder(Enum):
    LOAD = "load"
    SOLAR = "solar"
    WIND = "wind"

    def save(self, study_path: Path, area_id: str) -> None:
        ini_path = study_path / "input" / self.value / "prepro" / area_id / "settings.ini"
        IniWriter().write({}, ini_path)

        conversion_matrix = pd.DataFrame([[-9999999980506447872, 0, 9999999980506447872], [0, 0, 0]])
        ts_type = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_CONVERSION")
        write_timeseries(study_path, conversion_matrix, ts_type, area_id=area_id)

        data_matrix = pd.DataFrame(np.ones([12, 6]), dtype=int)
        data_matrix[2] = 0
        ts_type = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_DATA")
        write_timeseries(study_path, data_matrix, ts_type, area_id=area_id)

        ts_type = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_K")
        write_timeseries(study_path, pd.DataFrame([]), ts_type, area_id=area_id)

        ts_type = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_TRANSLATION")
        write_timeseries(study_path, pd.DataFrame([]), ts_type, area_id=area_id)
