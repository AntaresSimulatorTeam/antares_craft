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
import os

from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

from antares.craft.tools.time_series_tool import TimeSeriesFileType

default_data_matrix = np.zeros((365, 6), dtype=np.float64)
default_data_matrix.flags.writeable = False

default_modulation_matrix = np.zeros((8760, 4), dtype=np.float64)
default_modulation_matrix.flags.writeable = False

default_series = np.zeros((8760, 1), dtype=np.float64)
default_series.flags.writeable = False

default_mingen = np.zeros((8760, 8), dtype=np.float64)
default_mingen.flags.writeable = False

default_link_parameters = np.zeros((8760, 6), dtype=np.float64)
default_link_parameters.flags.writeable = False

default_series_with_ones = np.ones((8760, 1), dtype=np.float64)
default_series_with_ones.flags.writeable = False

default_mod = np.zeros((365, 1), dtype=np.float64)
default_mod.flags.writeable = False

default_energy = np.zeros((12, 5), dtype=np.float64)
default_energy.flags.writeable = False

default_reserves = np.zeros((8760, 4), dtype=np.float64)
default_reserves.flags.writeable = False

default_maxpower = np.zeros((365, 4), dtype=np.float64)
default_maxpower[:, 1] = 24
default_maxpower[:, 3] = 24
default_maxpower.flags.writeable = False

default_reservoir = np.zeros((365, 3), dtype=np.float64)
default_reservoir[:, 1] = 0.5
default_reservoir[:, 2] = 1
default_reservoir.flags.writeable = False

default_credit_modulation = np.ones((2, 100), dtype=np.float64)
default_credit_modulation.flags.writeable = False

default_water_values = np.zeros((365, 101), dtype=np.float64)
default_water_values.flags.writeable = False

default_inflow_pattern = np.ones((365, 1), dtype=np.float64)
default_inflow_pattern.flags.writeable = False


DEFAULT_MATRIX_MAPPING = {
    TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL: pd.DataFrame(),
    TimeSeriesFileType.BINDING_CONSTRAINT_GREATER: pd.DataFrame(),
    TimeSeriesFileType.BINDING_CONSTRAINT_LESS: pd.DataFrame(),
    TimeSeriesFileType.HYDRO_MAX_POWER: pd.DataFrame(default_maxpower),
    TimeSeriesFileType.HYDRO_RESERVOIR: pd.DataFrame(default_reservoir),
    TimeSeriesFileType.HYDRO_INFLOW_PATTERN: pd.DataFrame(default_inflow_pattern),
    TimeSeriesFileType.HYDRO_CREDITS_MODULATION: pd.DataFrame(default_credit_modulation),
    TimeSeriesFileType.HYDRO_WATER_VALUES: pd.DataFrame(default_water_values),
    TimeSeriesFileType.HYDRO_ROR: pd.DataFrame(default_series),
    TimeSeriesFileType.HYDRO_MOD: pd.DataFrame(default_mod),
    TimeSeriesFileType.HYDRO_MINGEN: pd.DataFrame(default_series),
    TimeSeriesFileType.HYDRO_ENERGY: pd.DataFrame(default_energy),
    TimeSeriesFileType.LINKS_CAPACITIES_DIRECT: pd.DataFrame(default_series_with_ones),
    TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT: pd.DataFrame(default_series_with_ones),
    TimeSeriesFileType.LINKS_PARAMETERS: pd.DataFrame(default_link_parameters),
    TimeSeriesFileType.LOAD: pd.DataFrame(default_series),
    TimeSeriesFileType.MISC_GEN: pd.DataFrame(default_mingen),
    TimeSeriesFileType.RENEWABLE_SERIES: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION: pd.DataFrame(default_series_with_ones),
    TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL: pd.DataFrame(default_series_with_ones),
    TimeSeriesFileType.ST_STORAGE_INFLOWS: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE: pd.DataFrame(default_series_with_ones),
    TimeSeriesFileType.ST_STORAGE_COST_INJECTION: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_COST_WITHDRAWAL: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_COST_VARIATION_INJECTION: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_COST_VARIATION_WITHDRAWAL: pd.DataFrame(default_series),
    TimeSeriesFileType.ST_STORAGE_COST_LEVEL: pd.DataFrame(default_series),
    TimeSeriesFileType.RESERVES: pd.DataFrame(default_reserves),
    TimeSeriesFileType.SOLAR: pd.DataFrame(default_series),
    TimeSeriesFileType.THERMAL_SERIES: pd.DataFrame(default_series),
    TimeSeriesFileType.THERMAL_DATA: pd.DataFrame(default_data_matrix),
    TimeSeriesFileType.THERMAL_MODULATION: pd.DataFrame(default_modulation_matrix),
    TimeSeriesFileType.THERMAL_CO2: pd.DataFrame(default_series),
    TimeSeriesFileType.THERMAL_FUEL: pd.DataFrame(default_series),
    TimeSeriesFileType.WIND: pd.DataFrame(default_series),
}


def read_timeseries(
    ts_file_type: TimeSeriesFileType,
    study_path: Path,
    area_id: Optional[str] = None,
    constraint_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    second_area_id: Optional[str] = None,
) -> pd.DataFrame:
    file_path = study_path / (
        ts_file_type.value
        if not (area_id or constraint_id or cluster_id or second_area_id)
        else ts_file_type.value.format(
            area_id=area_id, constraint_id=constraint_id, cluster_id=cluster_id, second_area_id=second_area_id
        )
    )
    if os.path.getsize(file_path) != 0:
        _time_series = pd.read_csv(file_path, sep="\t", header=None)
    else:
        _time_series = DEFAULT_MATRIX_MAPPING[ts_file_type]

    return _time_series


def write_timeseries(
    study_path: Path,
    series: Optional[pd.DataFrame],
    ts_file_type: TimeSeriesFileType,
    area_id: Optional[str] = None,
    cluster_id: Optional[str] = None,
    second_area_id: Optional[str] = None,
    constraint_id: Optional[str] = None,
) -> None:
    series = pd.DataFrame() if series is None else series
    format_kwargs = {}
    if area_id:
        format_kwargs["area_id"] = area_id
    if cluster_id:
        format_kwargs["cluster_id"] = cluster_id
    if second_area_id:
        format_kwargs["second_area_id"] = second_area_id
    if constraint_id:
        format_kwargs["constraint_id"] = constraint_id

    file_path = study_path / ts_file_type.value.format(**format_kwargs)

    file_path.parent.mkdir(parents=True, exist_ok=True)

    series.to_csv(file_path, sep="\t", header=False, index=False, encoding="utf-8")
