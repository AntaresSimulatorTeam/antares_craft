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
import numpy as np
import pandas as pd

from antares.craft import Study
from antares.craft.model.binding_constraint import BindingConstraintFrequency, BindingConstraintPropertiesUpdate
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
    def test_all_matrices(self, local_study_with_constraint: Study) -> None:
        area_fr = local_study_with_constraint.get_areas()["fr"]
        # Load
        assert area_fr.get_load_matrix().equals(pd.DataFrame(default_series))
        # Misc-gen
        assert area_fr.get_misc_gen_matrix().equals(pd.DataFrame(default_mingen))
        # Reserves
        assert area_fr.get_reserves_matrix().equals(pd.DataFrame(default_reserves))
        # Wind
        assert area_fr.get_wind_matrix().equals(pd.DataFrame(default_series))
        # Solar
        assert area_fr.get_solar_matrix().equals(pd.DataFrame(default_series))
        # Hydro
        assert area_fr.hydro.get_mod_series().equals(pd.DataFrame(default_mod))
        assert area_fr.hydro.get_ror_series().equals(pd.DataFrame(default_series))
        assert area_fr.hydro.get_energy().equals(pd.DataFrame(default_energy))
        assert area_fr.hydro.get_mingen().equals(pd.DataFrame(default_series))
        assert area_fr.hydro.get_reservoir().equals(pd.DataFrame(default_reservoir))
        assert area_fr.hydro.get_credit_modulations().equals(pd.DataFrame(default_credit_modulation))
        assert area_fr.hydro.get_maxpower().equals(pd.DataFrame(default_maxpower))
        assert area_fr.hydro.get_inflow_pattern().equals(pd.DataFrame(default_inflow_pattern))
        assert area_fr.hydro.get_water_values().equals(pd.DataFrame(default_water_values))
        # Binding constraint
        bc = local_study_with_constraint.get_binding_constraints()["test constraint"]
        default_hourly_matrix = pd.DataFrame(np.zeros((8784, 1)))
        assert bc.get_equal_term_matrix().equals(default_hourly_matrix)
        assert bc.get_greater_term_matrix().equals(default_hourly_matrix)
        assert bc.get_less_term_matrix().equals(default_hourly_matrix)
        bc.update_properties(BindingConstraintPropertiesUpdate(time_step=BindingConstraintFrequency.DAILY))
        default_daily_matrix = pd.DataFrame(np.zeros((366, 1)))
        assert bc.get_equal_term_matrix().equals(default_daily_matrix)
        assert bc.get_greater_term_matrix().equals(default_daily_matrix)
        assert bc.get_less_term_matrix().equals(default_daily_matrix)
        # Links
        link = local_study_with_constraint.get_links()["at / fr"]
        assert link.get_parameters().equals(pd.DataFrame(default_link_parameters))
        assert link.get_capacity_direct().equals(pd.DataFrame(default_series_with_ones))
        assert link.get_capacity_indirect().equals(pd.DataFrame(default_series_with_ones))
        # Renewables
        renewable = area_fr.get_renewables()["renewable cluster"]
        assert renewable.get_timeseries().equals(pd.DataFrame(default_series))
        # St storages
        storage = area_fr.get_st_storages()["short term storage"]
        assert storage.get_storage_inflows().equals(pd.DataFrame(default_series))
        assert storage.get_pmax_injection().equals(pd.DataFrame(default_series_with_ones))
        assert storage.get_pmax_withdrawal().equals(pd.DataFrame(default_series_with_ones))
        assert storage.get_lower_rule_curve().equals(pd.DataFrame(default_series))
        assert storage.get_upper_rule_curve().equals(pd.DataFrame(default_series_with_ones))
        # Thermal
        thermal = area_fr.get_thermals()["test thermal cluster"]
        assert thermal.get_series_matrix().equals(pd.DataFrame(default_series))
        assert thermal.get_fuel_cost_matrix().equals(pd.DataFrame(default_series))
        assert thermal.get_co2_cost_matrix().equals(pd.DataFrame(default_series))
        # Ensures the thermal cluster was created with specific prepro matrices
        default_data_matrix_creation = np.zeros((365, 6), dtype=np.float64)
        default_data_matrix_creation[:, :2] = 1
        assert thermal.get_prepro_data_matrix().equals(pd.DataFrame(default_data_matrix_creation))
        default_modulation_matrix_creation = np.ones((8760, 4), dtype=np.float64)
        default_modulation_matrix_creation[:, 3] = 0
        assert thermal.get_prepro_modulation_matrix().equals(pd.DataFrame(default_modulation_matrix_creation))
