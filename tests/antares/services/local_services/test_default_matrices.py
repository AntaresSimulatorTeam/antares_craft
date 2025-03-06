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
    default_data_matrix,
    default_energy,
    default_inflow_pattern,
    default_link_parameters,
    default_maxpower,
    default_mingen,
    default_mod,
    default_modulation_matrix,
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
        storage_inflow = storage.get_storage_inflows()
        assert storage_inflow.equals(pd.DataFrame(default_series))
        pmax_injection = storage.get_pmax_injection()
        assert pmax_injection.equals(pd.DataFrame(default_series_with_ones))
        pmax_withdrawal = storage.get_pmax_withdrawal()
        assert pmax_withdrawal.equals(pd.DataFrame(default_series_with_ones))
        lower_curve = storage.get_lower_rule_curve()
        assert lower_curve.equals(pd.DataFrame(default_series))
        upper_curve = storage.get_upper_rule_curve()
        assert upper_curve.equals(pd.DataFrame(default_series_with_ones))
        # Thermal
        thermal = area_fr.get_thermals()["test thermal cluster"]
        thermal_series = thermal.get_series_matrix()
        assert thermal_series.equals(pd.DataFrame(default_series))
        prepro_data = thermal.get_prepro_data_matrix()
        assert prepro_data.equals(pd.DataFrame(default_data_matrix))
        prepro_modulation = thermal.get_prepro_modulation_matrix()
        assert prepro_modulation.equals(pd.DataFrame(default_modulation_matrix))
        fuel_matrix = thermal.get_fuel_cost_matrix()
        assert fuel_matrix.equals(pd.DataFrame(default_series))
        co2_matrix = thermal.get_co2_cost_matrix()
        assert co2_matrix.equals(pd.DataFrame(default_series))
