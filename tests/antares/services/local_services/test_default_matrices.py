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

from antares.craft.tools.matrix_tool import (
    default_credit_modulation,
    default_energy,
    default_inflow_pattern,
    default_link_parameters,
    default_maxpower,
    default_mingen,
    default_mod,
    default_reserves,
    default_reservoir,
    default_series,
    default_series_with_ones,
    default_water_values,
)


class TestDefaultMatrices:
    def test_all_matrices(self, local_study_with_constraint):
        area_fr = local_study_with_constraint.get_areas()["fr"]
        # Load
        load = area_fr.get_load_matrix()
        assert load.equals(pd.DataFrame(default_series))
        # Misc-gen
        misc_gen = area_fr.get_misc_gen_matrix()
        assert misc_gen.equals(pd.DataFrame(default_mingen))
        # Reserves
        reserves = area_fr.get_reserves_matrix()
        assert reserves.equals(pd.DataFrame(default_reserves))
        # Wind
        wind = area_fr.get_wind_matrix()
        assert wind.equals(pd.DataFrame(default_series))
        # Solar
        solar = area_fr.get_solar_matrix()
        assert solar.equals(pd.DataFrame(default_series))
        # Hydro
        mod = area_fr.hydro.get_mod_series()
        assert mod.equals(pd.DataFrame(default_mod))
        ror = area_fr.hydro.get_ror_series()
        assert ror.equals(pd.DataFrame(default_series))
        energy = area_fr.hydro.get_energy()
        assert energy.equals(pd.DataFrame(default_energy))
        hydro_mingen = area_fr.hydro.get_mingen()
        assert hydro_mingen.equals(pd.DataFrame(default_series))
        reservoir = area_fr.hydro.get_reservoir()
        assert reservoir.equals(pd.DataFrame(default_reservoir))
        credit_modulation = area_fr.hydro.get_credit_modulations()
        assert credit_modulation.equals(pd.DataFrame(default_credit_modulation))
        hydro_max_power = area_fr.hydro.get_maxpower()
        assert hydro_max_power.equals(pd.DataFrame(default_maxpower))
        hydro_inflow = area_fr.hydro.get_inflow_pattern()
        assert hydro_inflow.equals(pd.DataFrame(default_inflow_pattern))
        water_values = area_fr.hydro.get_water_values()
        assert water_values.equals(pd.DataFrame(default_water_values))
        # Binding constraint
        # todo
        bc = local_study_with_constraint.get_binding_constraints()["test constraint"]
        bc.get_equal_term_matrix()
        bc.get_greater_term_matrix()
        bc.get_less_term_matrix()
        # Links
        link = local_study_with_constraint.get_links()["at / fr"]
        parameters = link.get_parameters()
        assert parameters.equals(pd.DataFrame(default_link_parameters))
        capa_direct = link.get_capacity_direct()
        assert capa_direct.equals(pd.DataFrame(default_series_with_ones))
        capa_indirect = link.get_capacity_indirect()
        assert capa_indirect.equals(pd.DataFrame(default_series_with_ones))
        # Renewables
        renewable = area_fr.get_renewables()["renewable cluster"]
        renewable_series = renewable.get_timeseries()
        assert renewable_series.equals(pd.DataFrame(default_series))
        # St storages
        storage = area_fr.get_st_storages()["short term storage"]
        storage.get_storage_inflows()
        storage.get_pmax_injection()
        storage.get_pmax_withdrawal()
        storage.get_lower_rule_curve()
        storage.get_upper_rule_curve()
        # Thermal
        thermal = area_fr.get_thermals()["test thermal cluster"]
        thermal.get_series_matrix()
        thermal.get_prepro_data_matrix()
        thermal.get_prepro_modulation_matrix()
        thermal.get_fuel_cost_matrix()
        thermal.get_co2_cost_matrix()

        """
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
            TimeSeriesFileType.RESERVES: pd.DataFrame(default_reserves),
            TimeSeriesFileType.SOLAR: pd.DataFrame(default_series),
            TimeSeriesFileType.THERMAL_SERIES: pd.DataFrame(default_series),
            TimeSeriesFileType.THERMAL_DATA: pd.DataFrame(default_data_matrix),
            TimeSeriesFileType.THERMAL_MODULATION: pd.DataFrame(default_modulation_matrix),
            TimeSeriesFileType.THERMAL_CO2: pd.DataFrame(default_series),
            TimeSeriesFileType.THERMAL_FUEL: pd.DataFrame(default_series),
            TimeSeriesFileType.WIND: pd.DataFrame(default_series),
        }
        """
