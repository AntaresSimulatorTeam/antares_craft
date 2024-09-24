import numpy as np
import pandas as pd
import pytest

from antares.tools.time_series_tool import TimeSeriesFile, TimeSeriesFileType


@pytest.fixture
def time_series_data():
    return pd.DataFrame(np.zeros([2, 3]))


@pytest.fixture
def time_series_file(tmp_path, time_series_data):
    return TimeSeriesFile(TimeSeriesFileType.RESERVES, tmp_path, "test", time_series_data)
