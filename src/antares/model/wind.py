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
from typing import Optional, Any

import pandas as pd

from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.time_series_tool import TimeSeries, ConversionFile, TimeSeriesFile, TimeSeriesFileType, DataFile


class Wind(TimeSeries):
    def __init__(
        self,
        *,
        study_path: Optional[Path] = None,
        area_id: Optional[str] = None,
        settings: Optional[IniFile] = None,
        conversion: Optional[TimeSeries] = None,
        data: Optional[TimeSeries] = None,
        k: Optional[TimeSeries] = None,
        translation: Optional[TimeSeries] = None,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        if study_path:
            self._settings = (
                settings if settings is not None else IniFile(study_path, IniFileTypes.WIND_SETTINGS_INI, area_id)
            )
            self._conversion = (
                conversion
                if conversion is not None
                else TimeSeries(
                    ConversionFile().data,
                    TimeSeriesFile(TimeSeriesFileType.WIND_CONVERSION, study_path, area_id, ConversionFile().data),
                )
            )
            self._data = (
                data
                if data is not None
                else TimeSeries(
                    DataFile().data, TimeSeriesFile(TimeSeriesFileType.WIND_DATA, study_path, area_id, DataFile().data)
                )
            )
            self._k = (
                k
                if k is not None
                else TimeSeries(
                    pd.DataFrame([]), TimeSeriesFile(TimeSeriesFileType.WIND_K, study_path, area_id, pd.DataFrame([]))
                )
            )
            self._translation = (
                translation
                if translation is not None
                else TimeSeries(
                    pd.DataFrame([]),
                    TimeSeriesFile(TimeSeriesFileType.WIND_TRANSLATION, study_path, area_id, pd.DataFrame([])),
                )
            )

    @property
    def settings(self) -> IniFile:
        return self._settings

    @property
    def conversion(self) -> TimeSeries:
        return self._conversion

    @property
    def data(self) -> TimeSeries:
        return self._data

    @property
    def k(self) -> TimeSeries:
        return self._k

    @property
    def translation(self) -> TimeSeries:
        return self._translation
