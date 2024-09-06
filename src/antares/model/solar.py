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

from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.time_series_tool import TimeSeries


class Solar(TimeSeries):
    def __init__(
        self,
        *,
        study_path: Optional[Path] = None,
        area_id: Optional[str] = None,
        settings: Optional[IniFile] = None,
        **kwargs,
    ) -> None:
        super().__init__(**kwargs)
        if study_path:
            self._settings = (
                settings if settings is not None else IniFile(study_path, IniFileTypes.SOLAR_SETTINGS_INI, area_id)
            )

    @property
    def settings(self):
        return self._settings
