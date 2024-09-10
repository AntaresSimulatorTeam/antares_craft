from pathlib import Path

import numpy as np
import pandas as pd

from antares.tools.ini_tool import IniFileTypes, IniFile
from antares.tools.time_series_tool import TimeSeriesFileType, TimeSeries, TimeSeriesFile


class PreproFolder:
    def __init__(self, folder: str, study_path: Path, area_id: str) -> None:
        folders = ["load", "solar", "wind"]
        if folder not in folders:
            raise ValueError(f"Folder must be one of the following: {', '.join(folders[:-1])}, and {folders[-1]}")
        if folder == "solar":
            settings = IniFileTypes.SOLAR_SETTINGS_INI
            conversion = TimeSeriesFileType.SOLAR_CONVERSION
            data = TimeSeriesFileType.SOLAR_DATA
            k = TimeSeriesFileType.SOLAR_K
            translation = TimeSeriesFileType.SOLAR_TRANSLATION
        elif folder == "wind":
            settings = IniFileTypes.WIND_SETTINGS_INI
            conversion = TimeSeriesFileType.WIND_CONVERSION
            data = TimeSeriesFileType.WIND_DATA
            k = TimeSeriesFileType.WIND_K
            translation = TimeSeriesFileType.WIND_TRANSLATION
        elif folder == "load":
            settings = IniFileTypes.LOAD_SETTINGS_INI
            conversion = TimeSeriesFileType.LOAD_CONVERSION
            data = TimeSeriesFileType.LOAD_DATA
            k = TimeSeriesFileType.LOAD_K
            translation = TimeSeriesFileType.LOAD_TRANSLATION

        self._settings = IniFile(study_path, settings, area_id)
        self._conversion = TimeSeries(
            ConversionFile().data,
            TimeSeriesFile(conversion, study_path, area_id, ConversionFile().data),
        )
        self._data = TimeSeries(DataFile().data, TimeSeriesFile(data, study_path, area_id, DataFile().data))
        self._k = TimeSeries(pd.DataFrame([]), TimeSeriesFile(k, study_path, area_id, pd.DataFrame([])))
        self._translation = TimeSeries(
            pd.DataFrame([]),
            TimeSeriesFile(translation, study_path, area_id, pd.DataFrame([])),
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


class ConversionFile:
    def __init__(self) -> None:
        self.data = pd.DataFrame([[-9999999980506447872, 0, 9999999980506447872], [0, 0, 0]])


class DataFile:
    def __init__(self) -> None:
        default_data = pd.DataFrame(np.ones([12, 6]))
        default_data[2] = 0
        self._data = default_data.astype(int)

    @property
    def data(self) -> pd.DataFrame:
        return self._data
