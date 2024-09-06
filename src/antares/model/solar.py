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
from typing import Any, Optional

from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.time_series_tool import TimeSeries


class Solar(TimeSeries):
    def __init__(
        self,
        *,
        study_path: Optional[Path] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        # Check if study is local
        if study_path is not None:
            self.correlation = IniFile(study_path, IniFileTypes.SOLAR_CORRELATION_INI)
            # If no file already exists set default properties
            if not self.correlation.ini_dict:
                self.correlation.ini_dict = self._correlation_defaults()
                self.correlation.write_ini_file()

    @staticmethod
    def _correlation_defaults() -> dict[str, dict[str, str]]:
        return {
            "general": {"mode": "annual"},
            "annual": {},
            "0": {},
            "1": {},
            "2": {},
            "3": {},
            "4": {},
            "5": {},
            "6": {},
            "7": {},
            "8": {},
            "9": {},
            "10": {},
            "11": {},
        }
