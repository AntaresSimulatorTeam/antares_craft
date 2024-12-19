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

from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import df_save
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class PreproFolder(Enum):
    LOAD = "load"
    SOLAR = "solar"
    WIND = "wind"

    def save(self, study_path: Path, area_id: str) -> None:
        IniFile(study_path, IniFileTypes.__getitem__(f"{self.value.upper()}_SETTINGS_INI"), area_id)

        conversion = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_CONVERSION").value.format(area_id=area_id)
        conversion_path = study_path.joinpath(conversion)
        conversion_matrix = pd.DataFrame([[-9999999980506447872, 0, 9999999980506447872], [0, 0, 0]])
        df_save(conversion_matrix, conversion_path)

        data = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_DATA").value.format(area_id=area_id)
        data_matrix = pd.DataFrame(np.ones([12, 6]), dtype=int)
        data_matrix[2] = 0
        data_path = study_path.joinpath(data)
        df_save(data_matrix, data_path)

        k = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_K").value.format(area_id=area_id)
        k_path = study_path.joinpath(k)
        k_matrix = pd.DataFrame([])
        df_save(k_matrix, k_path)

        translation = TimeSeriesFileType.__getitem__(f"{self.value.upper()}_TRANSLATION").value.format(area_id=area_id)
        translation_path = study_path.joinpath(translation)
        translation_matrix = pd.DataFrame([])
        df_save(translation_matrix, translation_path)
