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
from typing import Optional

from antares.craft.model.settings.adequacy_patch import PriceTakingOrder
from antares.craft.model.settings.advanced_parameters import (
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.craft.model.settings.general import (
    BuildingMode,
    GeneralParameters,
    Mode,
    Month,
    OutputChoices,
    OutputFormat,
    WeekDay,
)
from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, Field
from pydantic.alias_generators import to_camel


@all_optional_model
class AdequacyPatchParametersAPI(BaseModel, alias_generator=to_camel):
    enable_adequacy_patch: Optional[bool] = None
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool = True
    ntc_between_physical_areas_out_adequacy_patch: bool = True
    price_taking_order: PriceTakingOrder = Field(default=PriceTakingOrder.DENS, validate_default=True)
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    enable_first_step: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 0
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 3


@all_optional_model
class AdvancedAndSeedParametersAPI(BaseModel, alias_generator=to_camel):
    accuracy_on_correlation: set[OutputChoices]
    initial_reservoir_levels: InitialReservoirLevel
    hydro_heuristic_policy: HydroHeuristicPolicy
    hydro_pricing_mode: HydroPricingMode
    power_fluctuations: PowerFluctuation
    shedding_policy: SheddingPolicy
    unit_commitment_mode: UnitCommitmentMode
    number_of_cores_mode: SimulationCore
    renewable_generation_modelling: RenewableGenerationModeling
    seed_tsgen_wind: int
    seed_tsgen_load: int
    seed_tsgen_hydro: int
    seed_tsgen_thermal: int
    seed_tsgen_solar: int
    seed_tsnumbers: int
    seed_unsupplied_energy_costs: int
    seed_spilled_energy_costs: int
    seed_thermal_costs: int
    seed_hydro_costs: int
    seed_initial_reservoir_levels: int


@all_optional_model
class GeneralParametersAPI(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    mode: Mode = Field(default=Mode.ECONOMY, validate_default=True)
    horizon: str
    nb_years: int
    first_day: int
    last_day: int
    first_january: WeekDay
    first_month: Month
    first_week_day: WeekDay
    leap_year: bool
    year_by_year: bool
    building_mode: BuildingMode
    selection_mode: bool
    thematic_trimming: bool
    geographic_trimming: bool
    active_rules_scenario: str
    read_only: bool
    simulation_synthesis: bool
    mc_scenario: bool
    result_format: OutputFormat

    def from_user_model(self, user_class: GeneralParameters) -> "GeneralParametersAPI":
        pass

    def to_user_model(self, nb_ts_thermal: int) -> GeneralParameters:
        return GeneralParameters(
            mode=self.mode,
            horizon=self.horizon,
            nb_years=self.nb_years,
            simulation_start=self.first_day,
            simulation_end=self.last_day,
            january_first=self.first_january,
            first_month_in_year=self.first_month,
            first_week_day=self.first_week_day,
            leap_year=self.leap_year,
            year_by_year=self.year_by_year,
            simulation_synthesis=self.simulation_synthesis,
            building_mode=self.building_mode,
            user_playlist=self.selection_mode,
            thematic_trimming=self.thematic_trimming,
            geographic_trimming=self.geographic_trimming,
            nb_timeseries_thermal=nb_ts_thermal,
        )


@all_optional_model
class OptimizationParametersAPI(BaseModel, alias_generator=to_camel):
    simplex_optimization_range: SimplexOptimizationRange
    transmission_capacities: OptimizationTransmissionCapacities
    binding_constraints: bool
    hurdle_costs: bool
    thermal_clusters_min_stable_power: bool
    thermal_clusters_min_ud_time: bool
    day_ahead_reserve: bool
    strategic_reserve: bool
    spinning_reserve: bool
    primary_reserve: bool
    export_mps: ExportMPS
    include_exportstructure: bool
    unfeasible_problem_behavior: UnfeasibleProblemBehavior


@all_optional_model
class ThematicTrimmingParametersAPI(BaseModel, alias_generator=to_camel):
    ov_cost: bool
    op_cost: bool
    mrg_price: bool
    co2_emis: bool
    dtg_by_plant: bool
    balance: bool
    row_bal: bool
    psp: bool
    misc_ndg: bool
    load: bool
    h_ror: bool
    wind: bool
    solar: bool
    nuclear: bool
    lignite: bool
    coal: bool
    gas: bool
    oil: bool
    mix_fuel: bool
    misc_dtg: bool
    h_stor: bool
    h_pump: bool
    h_lev: bool
    h_infl: bool
    h_ovfl: bool
    h_val: bool
    h_cost: bool
    unsp_enrg: bool
    spil_enrg: bool
    lold: bool
    lolp: bool
    avl_dtg: bool
    dtg_mrg: bool
    max_mrg: bool
    np_cost: bool
    np_cost_by_plant: bool
    nodu: bool
    nodu_by_plant: bool
    flow_lin: bool
    ucap_lin: bool
    loop_flow: bool
    flow_quad: bool
    cong_fee_alg: bool
    cong_fee_abs: bool
    marg_cost: bool
    cong_prob_plus: bool
    cong_prob_minus: bool
    hurdle_cost: bool
    res_generation_by_plant: bool
    misc_dtg_2: bool
    misc_dtg_3: bool
    misc_dtg_4: bool
    wind_offshore: bool
    wind_onshore: bool
    solar_concrt: bool
    solar_pv: bool
    solar_rooft: bool
    renw_1: bool
    renw_2: bool
    renw_3: bool
    renw_4: bool
    dens: bool
    profit_by_plant: bool
    sts_inj_by_plant: bool
    sts_withdrawal_by_plant: bool
    sts_lvl_by_plant: bool
    psp_open_injection: bool
    psp_open_withdrawal: bool
    psp_open_level: bool
    psp_closed_injection: bool
    psp_closed_withdrawal: bool
    psp_closed_level: bool
    pondage_injection: bool
    pondage_withdrawal: bool
    pondage_level: bool
    battery_injection: bool
    battery_withdrawal: bool
    battery_level: bool
    other1_injection: bool
    other1_withdrawal: bool
    other1_level: bool
    other2_injection: bool
    other2_withdrawal: bool
    other2_level: bool
    other3_injection: bool
    other3_withdrawal: bool
    other3_level: bool
    other4_injection: bool
    other4_withdrawal: bool
    other4_level: bool
    other5_injection: bool
    other5_withdrawal: bool
    other5_level: bool
    sts_cashflow_by_cluster: bool
