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
        area_fr.get_solar_matrix()
        # Hydro
        area_fr.hydro.get_mod_series()
        area_fr.hydro.get_ror_series()
        area_fr.hydro.get_energy()
        area_fr.hydro.get_mingen()
        area_fr.hydro.get_reservoir()
        area_fr.hydro.get_credit_modulations()
        area_fr.hydro.get_maxpower()
        area_fr.hydro.get_inflow_pattern()
        area_fr.hydro.get_water_values()
        # Binding constraint
        bc = local_study_with_constraint.get_binding_constraints()["test constraint"]
        bc.get_equal_term_matrix()
        bc.get_greater_term_matrix()
        bc.get_less_term_matrix()
        # Links
        link = local_study_with_constraint.get_links()["at / fr"]
        link.get_parameters()
        link.get_capacity_direct()
        link.get_capacity_indirect()
        # Renewables
        renewable = area_fr.get_renewables()["renewable cluster"]
        renewable.get_timeseries()
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
