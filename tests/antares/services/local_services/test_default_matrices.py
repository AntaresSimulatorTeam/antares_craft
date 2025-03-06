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



import pandas as pd

from antares.craft.tools.time_series_tool import TimeSeriesFileType


class TestDefaultMatrices:
    def test_all_matrices(self, local_study_with_constraint):
        area_fr = local_study_with_constraint.get_areas()["fr"]
        # Load
        load = area_fr.get_load_matrix()
        print(load)
        # Misc-gen
        misc_gen = area_fr.get_misc_gen_matrix()
        print(misc_gen)
        # Reserves
        reserves = area_fr.get_reserves_matrix()
        print(reserves)
        # Wind
        wind = area_fr.get_wind_matrix()
        print(wind)
        # Solar
        solar = area_fr.get_solar_matrix()
        print(solar)
        # Hydro

        # Binding constraint

        # Links

        # Renewables

        # St storages

        # Thermal

        DEFAULT_MATRIX_MAPPING = {
            TimeSeriesFileType.BINDING_CONSTRAINT_EQUAL: pd.DataFrame(),
            TimeSeriesFileType.BINDING_CONSTRAINT_GREATER: pd.DataFrame(),
            TimeSeriesFileType.BINDING_CONSTRAINT_LESS: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_MAX_POWER: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_RESERVOIR: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_INFLOW_PATTERN: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_CREDITS_MODULATION: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_WATER_VALUES: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_ROR: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_MOD: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_MINGEN: pd.DataFrame(),
            TimeSeriesFileType.HYDRO_ENERGY: pd.DataFrame(),
            TimeSeriesFileType.LINKS_CAPACITIES_DIRECT: pd.DataFrame(),
            TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT: pd.DataFrame(),
            TimeSeriesFileType.LINKS_PARAMETERS: pd.DataFrame(),
            TimeSeriesFileType.RENEWABLE_DATA_SERIES: pd.DataFrame(),
            TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION: pd.DataFrame(),
            TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL: pd.DataFrame(),
            TimeSeriesFileType.ST_STORAGE_INFLOWS: pd.DataFrame(),
            TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE: pd.DataFrame(),
            TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE: pd.DataFrame(),
            TimeSeriesFileType.THERMAL_SERIES: pd.DataFrame(),
            TimeSeriesFileType.THERMAL_DATA: pd.DataFrame(),
            TimeSeriesFileType.THERMAL_MODULATION: pd.DataFrame(),
            TimeSeriesFileType.THERMAL_CO2: pd.DataFrame(),
            TimeSeriesFileType.THERMAL_FUEL: pd.DataFrame(),
        }
