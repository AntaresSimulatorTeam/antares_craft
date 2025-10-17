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
import ast

from dataclasses import asdict
from typing import Any, Optional, Sequence, cast

from pydantic import field_validator

from antares.craft.model.settings.adequacy_patch import (
    AdequacyPatchParameters,
    AdequacyPatchParametersUpdate,
    PriceTakingOrder,
)
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParameters,
    AdvancedParametersUpdate,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SeedParameters,
    SeedParametersUpdate,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.craft.model.settings.general import (
    BuildingMode,
    GeneralParameters,
    GeneralParametersUpdate,
    Mode,
    Month,
    OutputChoices,
    WeekDay,
)
from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationParameters,
    OptimizationParametersUpdate,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.service.utils import check_field_is_not_null
from antares.craft.tools.contents_tool import EnumIgnoreCase

AdequacyPatchParametersType = AdequacyPatchParameters | AdequacyPatchParametersUpdate


class AdequacyPatchParametersAPI(APIBaseModel):
    enable_adequacy_patch: bool | None = None
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool | None = None
    ntc_between_physical_areas_out_adequacy_patch: bool | None = None
    price_taking_order: PriceTakingOrder | None = None
    include_hurdle_cost_csr: bool | None = None
    check_csr_cost_function: bool | None = None
    enable_first_step: bool | None = None
    threshold_initiate_curtailment_sharing_rule: int | None = None
    threshold_display_local_matching_rule_violations: int | None = None
    threshold_csr_variable_bounds_relaxation: int | None = None

    @staticmethod
    def from_user_model(user_class: AdequacyPatchParametersType) -> "AdequacyPatchParametersAPI":
        user_dict = asdict(user_class)
        user_dict["enable_adequacy_patch"] = user_dict.pop("include_adq_patch")
        user_dict["ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch"] = user_dict.pop(
            "set_to_null_ntc_from_physical_out_to_physical_in_for_first_step"
        )
        user_dict["ntc_between_physical_areas_out_adequacy_patch"] = user_dict.pop(
            "set_to_null_ntc_between_physical_out_for_first_step"
        )
        return AdequacyPatchParametersAPI.model_validate(user_dict)

    def to_user_model(self) -> AdequacyPatchParameters:
        return AdequacyPatchParameters(
            include_adq_patch=check_field_is_not_null(self.enable_adequacy_patch),
            set_to_null_ntc_from_physical_out_to_physical_in_for_first_step=check_field_is_not_null(
                self.ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch
            ),
            price_taking_order=check_field_is_not_null(self.price_taking_order),
            include_hurdle_cost_csr=check_field_is_not_null(self.include_hurdle_cost_csr),
            check_csr_cost_function=check_field_is_not_null(self.check_csr_cost_function),
            threshold_initiate_curtailment_sharing_rule=check_field_is_not_null(
                self.threshold_initiate_curtailment_sharing_rule
            ),
            threshold_display_local_matching_rule_violations=check_field_is_not_null(
                self.threshold_display_local_matching_rule_violations
            ),
            threshold_csr_variable_bounds_relaxation=check_field_is_not_null(
                self.threshold_csr_variable_bounds_relaxation
            ),
            set_to_null_ntc_between_physical_out_for_first_step=self.ntc_between_physical_areas_out_adequacy_patch,
        )


def parse_adequacy_patch_parameters_api(data: Any) -> AdequacyPatchParameters:
    return AdequacyPatchParametersAPI.model_validate(data).to_user_model()


def serialize_adequacy_patch_parameters_api(parameters: AdequacyPatchParametersType) -> dict[str, Any]:
    adequacy_patch_api_model = AdequacyPatchParametersAPI.from_user_model(parameters)
    return adequacy_patch_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)


AdvancedParametersType = AdvancedParameters | AdvancedParametersUpdate
SeedParametersType = SeedParameters | SeedParametersUpdate


class AdvancedAndSeedParametersAPI(APIBaseModel):
    accuracy_on_correlation: set[OutputChoices] | None = None
    initial_reservoir_levels: InitialReservoirLevel | None = None
    hydro_heuristic_policy: HydroHeuristicPolicy | None = None
    hydro_pricing_mode: HydroPricingMode | None = None
    power_fluctuations: PowerFluctuation | None = None
    shedding_policy: SheddingPolicy | None = None
    unit_commitment_mode: UnitCommitmentMode | None = None
    number_of_cores_mode: SimulationCore | None = None
    renewable_generation_modelling: RenewableGenerationModeling | None = None
    day_ahead_reserve_management: Any | None = None
    seed_tsgen_wind: int | None = None
    seed_tsgen_load: int | None = None
    seed_tsgen_hydro: int | None = None
    seed_tsgen_thermal: int | None = None
    seed_tsgen_solar: int | None = None
    seed_tsnumbers: int | None = None
    seed_unsupplied_energy_costs: int | None = None
    seed_spilled_energy_costs: int | None = None
    seed_thermal_costs: int | None = None
    seed_hydro_costs: int | None = None
    seed_initial_reservoir_levels: int | None = None

    @field_validator("accuracy_on_correlation", mode="before")
    def validate_accuracy_on_correlation(cls, v: Any) -> Sequence[str] | set[str]:
        if not v:
            return set()
        if isinstance(v, set):
            return v
        return cast(Sequence[str], ast.literal_eval(v))

    @staticmethod
    def from_user_model(
        advanced_parameters: Optional[AdvancedParametersType] = None,
        seed_parameters: Optional[SeedParametersType] = None,
    ) -> "AdvancedAndSeedParametersAPI":
        advanced_parameters_dict = asdict(advanced_parameters) if advanced_parameters else {}
        seed_parameters_dict = asdict(seed_parameters) if seed_parameters else {}
        api_dict = advanced_parameters_dict | seed_parameters_dict
        return AdvancedAndSeedParametersAPI.model_validate(api_dict)

    def to_user_advanced_parameters_model(self) -> AdvancedParameters:
        return AdvancedParameters(
            hydro_heuristic_policy=check_field_is_not_null(self.hydro_heuristic_policy),
            hydro_pricing_mode=check_field_is_not_null(self.hydro_pricing_mode),
            power_fluctuations=check_field_is_not_null(self.power_fluctuations),
            shedding_policy=check_field_is_not_null(self.shedding_policy),
            unit_commitment_mode=check_field_is_not_null(self.unit_commitment_mode),
            number_of_cores_mode=check_field_is_not_null(self.number_of_cores_mode),
            renewable_generation_modelling=check_field_is_not_null(self.renewable_generation_modelling),
            accuracy_on_correlation=check_field_is_not_null(self.accuracy_on_correlation),
            initial_reservoir_levels=self.initial_reservoir_levels,
        )

    def to_user_seed_parameters_model(self) -> SeedParameters:
        return SeedParameters(
            seed_tsgen_thermal=check_field_is_not_null(self.seed_tsgen_thermal),
            seed_tsnumbers=check_field_is_not_null(self.seed_tsnumbers),
            seed_unsupplied_energy_costs=check_field_is_not_null(self.seed_unsupplied_energy_costs),
            seed_spilled_energy_costs=check_field_is_not_null(self.seed_spilled_energy_costs),
            seed_thermal_costs=check_field_is_not_null(self.seed_thermal_costs),
            seed_hydro_costs=check_field_is_not_null(self.seed_hydro_costs),
            seed_initial_reservoir_levels=check_field_is_not_null(self.seed_initial_reservoir_levels),
        )


def parse_advanced_and_seed_parameters_api(data: Any) -> tuple[AdvancedParameters, SeedParameters]:
    advanced_parameters_api_model = AdvancedAndSeedParametersAPI.model_validate(data)
    seed_parameters = advanced_parameters_api_model.to_user_seed_parameters_model()
    advanced_parameters = advanced_parameters_api_model.to_user_advanced_parameters_model()
    return advanced_parameters, seed_parameters


def serialize_advanced_and_seed_parameters_api(
    advanced_parameters: Optional[AdvancedParametersType] = None, seed_parameters: Optional[SeedParametersType] = None
) -> dict[str, Any]:
    advanced_api_model = AdvancedAndSeedParametersAPI.from_user_model(advanced_parameters, seed_parameters)
    body = advanced_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
    if "accuracyOnCorrelation" in body:
        body["accuracyOnCorrelation"] = ", ".join(corr for corr in body["accuracyOnCorrelation"])
    return body


GeneralParametersType = GeneralParameters | GeneralParametersUpdate


class OutputFormat(EnumIgnoreCase):
    TXT = "txt-files"
    ZIP = "zip-files"


class GeneralParametersAPI(APIBaseModel):
    mode: Mode | None = None
    horizon: str | None = None
    nb_years: int | None = None
    first_day: int | None = None
    last_day: int | None = None
    first_january: WeekDay | None = None
    first_month: Month | None = None
    first_week_day: WeekDay | None = None
    leap_year: bool | None = None
    year_by_year: bool | None = None
    building_mode: BuildingMode | None = None
    selection_mode: bool | None = None
    thematic_trimming: bool | None = None
    geographic_trimming: bool | None = None
    active_rules_scenario: str | None = None
    read_only: bool | None = None
    simulation_synthesis: bool | None = None
    mc_scenario: bool | None = None
    result_format: OutputFormat | None = None

    @field_validator("horizon", mode="before")
    def transform_horizon_to_str(cls, val: str | int | None) -> Optional[str]:
        # horizon can be returned as an int by AntaresWeb
        return str(val) if val is not None else val

    @staticmethod
    def from_user_model(user_class: GeneralParametersType) -> "GeneralParametersAPI":
        user_dict = asdict(user_class)
        user_dict["first_day"] = user_dict.pop("simulation_start")
        user_dict["last_day"] = user_dict.pop("simulation_end")
        user_dict["first_january"] = user_dict.pop("january_first")
        user_dict["first_month"] = user_dict.pop("first_month_in_year")
        user_dict["selection_mode"] = user_dict.pop("user_playlist")
        user_dict["mc_scenario"] = user_dict.pop("store_new_set")
        user_dict.pop("nb_timeseries_thermal")
        return GeneralParametersAPI.model_validate(user_dict)

    def to_user_model(self, nb_ts_thermal: int) -> GeneralParameters:
        return GeneralParameters(
            mode=check_field_is_not_null(self.mode),
            horizon=check_field_is_not_null(self.horizon),
            nb_years=check_field_is_not_null(self.nb_years),
            simulation_start=check_field_is_not_null(self.first_day),
            simulation_end=check_field_is_not_null(self.last_day),
            january_first=check_field_is_not_null(self.first_january),
            first_month_in_year=check_field_is_not_null(self.first_month),
            first_week_day=check_field_is_not_null(self.first_week_day),
            leap_year=check_field_is_not_null(self.leap_year),
            year_by_year=check_field_is_not_null(self.year_by_year),
            simulation_synthesis=check_field_is_not_null(self.simulation_synthesis),
            building_mode=check_field_is_not_null(self.building_mode),
            user_playlist=check_field_is_not_null(self.selection_mode),
            thematic_trimming=check_field_is_not_null(self.thematic_trimming),
            geographic_trimming=check_field_is_not_null(self.geographic_trimming),
            store_new_set=check_field_is_not_null(self.mc_scenario),
            nb_timeseries_thermal=nb_ts_thermal,
        )


def parse_general_parameters_api(data: Any, nb_ts_thermal: int) -> GeneralParameters:
    return GeneralParametersAPI.model_validate(data).to_user_model(nb_ts_thermal)


def serialize_general_parameters_api(parameters: GeneralParametersType) -> dict[str, Any]:
    general_api_model = GeneralParametersAPI.from_user_model(parameters)
    return general_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)


OptimizationParametersType = OptimizationParameters | OptimizationParametersUpdate


class OptimizationParametersAPI(APIBaseModel):
    simplex_optimization_range: SimplexOptimizationRange | None = None
    transmission_capacities: OptimizationTransmissionCapacities | None = None
    binding_constraints: bool | None = None
    hurdle_costs: bool | None = None
    thermal_clusters_min_stable_power: bool | None = None
    thermal_clusters_min_ud_time: bool | None = None
    day_ahead_reserve: bool | None = None
    strategic_reserve: bool | None = None
    spinning_reserve: bool | None = None
    primary_reserve: bool | None = None
    export_mps: ExportMPS | None = None
    unfeasible_problem_behavior: UnfeasibleProblemBehavior | None = None

    @staticmethod
    def from_user_model(user_class: OptimizationParametersType) -> "OptimizationParametersAPI":
        user_dict = asdict(user_class)
        user_dict["simplex_optimization_range"] = user_dict.pop("simplex_range")
        user_dict["binding_constraints"] = user_dict.pop("include_constraints")
        user_dict["hurdle_costs"] = user_dict.pop("include_hurdlecosts")
        user_dict["thermal_clusters_min_stable_power"] = user_dict.pop("include_tc_minstablepower")
        user_dict["thermal_clusters_min_ud_time"] = user_dict.pop("include_tc_min_ud_time")
        user_dict["day_ahead_reserve"] = user_dict.pop("include_dayahead")
        user_dict["strategic_reserve"] = user_dict.pop("include_strategicreserve")
        user_dict["spinning_reserve"] = user_dict.pop("include_spinningreserve")
        user_dict["primary_reserve"] = user_dict.pop("include_primaryreserve")
        user_dict["export_mps"] = user_dict.pop("include_exportmps")
        user_dict["unfeasible_problem_behavior"] = user_dict.pop("include_unfeasible_problem_behavior")
        return OptimizationParametersAPI.model_validate(user_dict)

    def to_user_model(self) -> OptimizationParameters:
        return OptimizationParameters(
            simplex_range=check_field_is_not_null(self.simplex_optimization_range),
            transmission_capacities=check_field_is_not_null(self.transmission_capacities),
            include_constraints=check_field_is_not_null(self.binding_constraints),
            include_hurdlecosts=check_field_is_not_null(self.hurdle_costs),
            include_tc_minstablepower=check_field_is_not_null(self.thermal_clusters_min_stable_power),
            include_tc_min_ud_time=check_field_is_not_null(self.thermal_clusters_min_ud_time),
            include_dayahead=check_field_is_not_null(self.day_ahead_reserve),
            include_strategicreserve=check_field_is_not_null(self.strategic_reserve),
            include_spinningreserve=check_field_is_not_null(self.spinning_reserve),
            include_primaryreserve=check_field_is_not_null(self.primary_reserve),
            include_exportmps=check_field_is_not_null(self.export_mps),
            include_unfeasible_problem_behavior=check_field_is_not_null(self.unfeasible_problem_behavior),
        )


def parse_optimization_parameters_api(data: Any) -> OptimizationParameters:
    return OptimizationParametersAPI.model_validate(data).to_user_model()


def serialize_optimization_parameters_api(parameters: OptimizationParameters) -> dict[str, Any]:
    optimization_api_model = OptimizationParametersAPI.from_user_model(parameters)
    body = optimization_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
    return body


class ThematicTrimmingParametersAPI(APIBaseModel):
    ov_cost: bool | None = None
    op_cost: bool | None = None
    mrg_price: bool | None = None
    co2_emis: bool | None = None
    dtg_by_plant: bool | None = None
    balance: bool | None = None
    row_bal: bool | None = None
    psp: bool | None = None
    misc_ndg: bool | None = None
    load: bool | None = None
    h_ror: bool | None = None
    wind: bool | None = None
    solar: bool | None = None
    nuclear: bool | None = None
    lignite: bool | None = None
    coal: bool | None = None
    gas: bool | None = None
    oil: bool | None = None
    mix_fuel: bool | None = None
    misc_dtg: bool | None = None
    h_stor: bool | None = None
    h_pump: bool | None = None
    h_lev: bool | None = None
    h_infl: bool | None = None
    h_ovfl: bool | None = None
    h_val: bool | None = None
    h_cost: bool | None = None
    unsp_enrg: bool | None = None
    spil_enrg: bool | None = None
    lold: bool | None = None
    lolp: bool | None = None
    avl_dtg: bool | None = None
    dtg_mrg: bool | None = None
    max_mrg: bool | None = None
    np_cost: bool | None = None
    np_cost_by_plant: bool | None = None
    nodu: bool | None = None
    nodu_by_plant: bool | None = None
    flow_lin: bool | None = None
    ucap_lin: bool | None = None
    loop_flow: bool | None = None
    flow_quad: bool | None = None
    cong_fee_alg: bool | None = None
    cong_fee_abs: bool | None = None
    marg_cost: bool | None = None
    cong_prob_plus: bool | None = None
    cong_prob_minus: bool | None = None
    hurdle_cost: bool | None = None
    res_generation_by_plant: bool | None = None
    misc_dtg_2: bool | None = None
    misc_dtg_3: bool | None = None
    misc_dtg_4: bool | None = None
    wind_offshore: bool | None = None
    wind_onshore: bool | None = None
    solar_concrt: bool | None = None
    solar_pv: bool | None = None
    solar_rooft: bool | None = None
    renw_1: bool | None = None
    renw_2: bool | None = None
    renw_3: bool | None = None
    renw_4: bool | None = None
    dens: bool | None = None
    profit_by_plant: bool | None = None
    sts_inj_by_plant: bool | None = None
    sts_withdrawal_by_plant: bool | None = None
    sts_lvl_by_plant: bool | None = None
    psp_open_injection: bool | None = None
    psp_open_withdrawal: bool | None = None
    psp_open_level: bool | None = None
    psp_closed_injection: bool | None = None
    psp_closed_withdrawal: bool | None = None
    psp_closed_level: bool | None = None
    pondage_injection: bool | None = None
    pondage_withdrawal: bool | None = None
    pondage_level: bool | None = None
    battery_injection: bool | None = None
    battery_withdrawal: bool | None = None
    battery_level: bool | None = None
    other1_injection: bool | None = None
    other1_withdrawal: bool | None = None
    other1_level: bool | None = None
    other2_injection: bool | None = None
    other2_withdrawal: bool | None = None
    other2_level: bool | None = None
    other3_injection: bool | None = None
    other3_withdrawal: bool | None = None
    other3_level: bool | None = None
    other4_injection: bool | None = None
    other4_withdrawal: bool | None = None
    other4_level: bool | None = None
    other5_injection: bool | None = None
    other5_withdrawal: bool | None = None
    other5_level: bool | None = None
    sts_cashflow_by_cluster: bool | None = None
    npcap_hours: bool | None = None
    bc_marg_cost: bool | None = None
    # Since v9.2
    sts_by_group: bool | None = None
    # Since v9.3
    dispatch_gen: bool | None = None
    renewable_gen: bool | None = None

    @staticmethod
    def from_user_model(user_class: ThematicTrimmingParameters) -> "ThematicTrimmingParametersAPI":
        user_dict = asdict(user_class)
        return ThematicTrimmingParametersAPI.model_validate(user_dict)

    def to_user_model(self) -> ThematicTrimmingParameters:
        return ThematicTrimmingParameters(
            ov_cost=check_field_is_not_null(self.ov_cost),
            op_cost=check_field_is_not_null(self.op_cost),
            mrg_price=check_field_is_not_null(self.mrg_price),
            co2_emis=check_field_is_not_null(self.co2_emis),
            dtg_by_plant=check_field_is_not_null(self.dtg_by_plant),
            balance=check_field_is_not_null(self.balance),
            row_bal=check_field_is_not_null(self.row_bal),
            psp=check_field_is_not_null(self.psp),
            misc_ndg=check_field_is_not_null(self.misc_ndg),
            load=check_field_is_not_null(self.load),
            h_ror=check_field_is_not_null(self.h_ror),
            wind=check_field_is_not_null(self.wind),
            h_stor=check_field_is_not_null(self.h_stor),
            h_pump=check_field_is_not_null(self.h_pump),
            h_lev=check_field_is_not_null(self.h_lev),
            h_infl=check_field_is_not_null(self.h_infl),
            h_ovfl=check_field_is_not_null(self.h_ovfl),
            h_val=check_field_is_not_null(self.h_val),
            h_cost=check_field_is_not_null(self.h_cost),
            unsp_enrg=check_field_is_not_null(self.unsp_enrg),
            spil_enrg=check_field_is_not_null(self.spil_enrg),
            lold=check_field_is_not_null(self.lold),
            lolp=check_field_is_not_null(self.lolp),
            avl_dtg=check_field_is_not_null(self.avl_dtg),
            dtg_mrg=check_field_is_not_null(self.dtg_mrg),
            max_mrg=check_field_is_not_null(self.max_mrg),
            np_cost=check_field_is_not_null(self.np_cost),
            np_cost_by_plant=check_field_is_not_null(self.np_cost_by_plant),
            nodu=check_field_is_not_null(self.nodu),
            nodu_by_plant=check_field_is_not_null(self.nodu_by_plant),
            flow_lin=check_field_is_not_null(self.flow_lin),
            ucap_lin=check_field_is_not_null(self.ucap_lin),
            loop_flow=check_field_is_not_null(self.loop_flow),
            flow_quad=check_field_is_not_null(self.flow_quad),
            cong_fee_alg=check_field_is_not_null(self.cong_fee_alg),
            cong_fee_abs=check_field_is_not_null(self.cong_fee_abs),
            marg_cost=check_field_is_not_null(self.marg_cost),
            cong_prob_plus=check_field_is_not_null(self.cong_prob_plus),
            cong_prob_minus=check_field_is_not_null(self.cong_prob_minus),
            hurdle_cost=check_field_is_not_null(self.hurdle_cost),
            res_generation_by_plant=check_field_is_not_null(self.res_generation_by_plant),
            dens=check_field_is_not_null(self.dens),
            profit_by_plant=check_field_is_not_null(self.profit_by_plant),
            sts_inj_by_plant=check_field_is_not_null(self.sts_inj_by_plant),
            sts_withdrawal_by_plant=check_field_is_not_null(self.sts_withdrawal_by_plant),
            sts_lvl_by_plant=check_field_is_not_null(self.sts_lvl_by_plant),
            sts_cashflow_by_cluster=check_field_is_not_null(self.sts_cashflow_by_cluster),
            npcap_hours=check_field_is_not_null(self.npcap_hours),
            bc_marg_cost=check_field_is_not_null(self.bc_marg_cost),
            # Optional fields
            solar=self.solar,
            nuclear=self.nuclear,
            lignite=self.lignite,
            coal=self.coal,
            gas=self.gas,
            oil=self.oil,
            mix_fuel=self.mix_fuel,
            misc_dtg=self.misc_dtg,
            misc_dtg_2=self.misc_dtg_2,
            misc_dtg_3=self.misc_dtg_3,
            misc_dtg_4=self.misc_dtg_4,
            wind_offshore=self.wind_offshore,
            wind_onshore=self.wind_onshore,
            solar_concrt=self.solar_concrt,
            solar_pv=self.solar_pv,
            solar_rooft=self.solar_rooft,
            renw_1=self.renw_1,
            renw_2=self.renw_2,
            renw_3=self.renw_3,
            renw_4=self.renw_4,
            sts_by_group=self.sts_by_group,
            psp_open_injection=self.psp_open_injection,
            psp_open_withdrawal=self.psp_open_withdrawal,
            psp_open_level=self.psp_open_level,
            psp_closed_injection=self.psp_closed_injection,
            psp_closed_withdrawal=self.psp_closed_withdrawal,
            psp_closed_level=self.psp_closed_level,
            pondage_injection=self.pondage_injection,
            pondage_withdrawal=self.pondage_withdrawal,
            pondage_level=self.pondage_level,
            battery_injection=self.battery_injection,
            battery_withdrawal=self.battery_withdrawal,
            battery_level=self.battery_level,
            other1_injection=self.other1_injection,
            other1_withdrawal=self.other1_withdrawal,
            other1_level=self.other1_level,
            other2_injection=self.other2_injection,
            other2_withdrawal=self.other2_withdrawal,
            other2_level=self.other2_level,
            other3_injection=self.other3_injection,
            other3_withdrawal=self.other3_withdrawal,
            other3_level=self.other3_level,
            other4_injection=self.other4_injection,
            other4_withdrawal=self.other4_withdrawal,
            other4_level=self.other4_level,
            other5_injection=self.other5_injection,
            other5_withdrawal=self.other5_withdrawal,
            other5_level=self.other5_level,
            renewable_gen=self.renewable_gen,
            dispatch_gen=self.dispatch_gen,
        )


def parse_thematic_trimming_api(data: Any) -> ThematicTrimmingParameters:
    return ThematicTrimmingParametersAPI.model_validate(data).to_user_model()


def serialize_thematic_trimming_api(thematic_trimming: ThematicTrimmingParameters) -> dict[str, Any]:
    return ThematicTrimmingParametersAPI.from_user_model(thematic_trimming).model_dump(mode="json", exclude_none=True)
