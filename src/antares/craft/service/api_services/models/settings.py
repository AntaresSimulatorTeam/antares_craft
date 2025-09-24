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

from pydantic import Field, field_validator

from antares.craft.exceptions.exceptions import APIError
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
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.contents_tool import EnumIgnoreCase

AdequacyPatchParametersType = AdequacyPatchParameters | AdequacyPatchParametersUpdate


@all_optional_model
class AdequacyPatchParametersAPI(APIBaseModel):
    enable_adequacy_patch: bool
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool
    ntc_between_physical_areas_out_adequacy_patch: bool
    price_taking_order: PriceTakingOrder
    include_hurdle_cost_csr: bool
    check_csr_cost_function: bool
    enable_first_step: bool
    threshold_initiate_curtailment_sharing_rule: int
    threshold_display_local_matching_rule_violations: int
    threshold_csr_variable_bounds_relaxation: int

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
            include_adq_patch=self.enable_adequacy_patch,
            set_to_null_ntc_from_physical_out_to_physical_in_for_first_step=self.ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch,
            set_to_null_ntc_between_physical_out_for_first_step=self.ntc_between_physical_areas_out_adequacy_patch,
            price_taking_order=self.price_taking_order,
            include_hurdle_cost_csr=self.include_hurdle_cost_csr,
            check_csr_cost_function=self.check_csr_cost_function,
            threshold_initiate_curtailment_sharing_rule=self.threshold_initiate_curtailment_sharing_rule,
            threshold_display_local_matching_rule_violations=self.threshold_display_local_matching_rule_violations,
            threshold_csr_variable_bounds_relaxation=self.threshold_csr_variable_bounds_relaxation,
        )


def parse_adequacy_patch_parameters_api(data: Any) -> AdequacyPatchParameters:
    return AdequacyPatchParametersAPI.model_validate(data).to_user_model()


def serialize_adequacy_patch_parameters_api(parameters: AdequacyPatchParametersType) -> dict[str, Any]:
    adequacy_patch_api_model = AdequacyPatchParametersAPI.from_user_model(parameters)
    return adequacy_patch_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)


AdvancedParametersType = AdvancedParameters | AdvancedParametersUpdate
SeedParametersType = SeedParameters | SeedParametersUpdate


@all_optional_model
class AdvancedAndSeedParametersAPI(APIBaseModel):
    accuracy_on_correlation: set[OutputChoices]
    initial_reservoir_levels: InitialReservoirLevel
    hydro_heuristic_policy: HydroHeuristicPolicy
    hydro_pricing_mode: HydroPricingMode
    power_fluctuations: PowerFluctuation
    shedding_policy: SheddingPolicy
    unit_commitment_mode: UnitCommitmentMode
    number_of_cores_mode: SimulationCore
    renewable_generation_modelling: RenewableGenerationModeling
    day_ahead_reserve_management: Any
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
            initial_reservoir_levels=self.initial_reservoir_levels,
            hydro_heuristic_policy=self.hydro_heuristic_policy,
            hydro_pricing_mode=self.hydro_pricing_mode,
            power_fluctuations=self.power_fluctuations,
            shedding_policy=self.shedding_policy,
            unit_commitment_mode=self.unit_commitment_mode,
            number_of_cores_mode=self.number_of_cores_mode,
            renewable_generation_modelling=self.renewable_generation_modelling,
            accuracy_on_correlation=self.accuracy_on_correlation,
        )

    def to_user_seed_parameters_model(self) -> SeedParameters:
        return SeedParameters(
            seed_tsgen_thermal=self.seed_tsgen_thermal,
            seed_tsnumbers=self.seed_tsnumbers,
            seed_unsupplied_energy_costs=self.seed_unsupplied_energy_costs,
            seed_spilled_energy_costs=self.seed_spilled_energy_costs,
            seed_thermal_costs=self.seed_thermal_costs,
            seed_hydro_costs=self.seed_hydro_costs,
            seed_initial_reservoir_levels=self.seed_initial_reservoir_levels,
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


@all_optional_model
class GeneralParametersAPI(APIBaseModel):
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
            store_new_set=self.mc_scenario,
            nb_timeseries_thermal=nb_ts_thermal,
        )


def parse_general_parameters_api(data: Any, nb_ts_thermal: int) -> GeneralParameters:
    return GeneralParametersAPI.model_validate(data).to_user_model(nb_ts_thermal)


def serialize_general_parameters_api(parameters: GeneralParametersType) -> dict[str, Any]:
    general_api_model = GeneralParametersAPI.from_user_model(parameters)
    return general_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)


OptimizationParametersType = OptimizationParameters | OptimizationParametersUpdate


@all_optional_model
class OptimizationParametersAPI(APIBaseModel):
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
        user_dict["include_exportstructure"] = user_dict.pop("include_exportstructure")
        user_dict["unfeasible_problem_behavior"] = user_dict.pop("include_unfeasible_problem_behavior")
        return OptimizationParametersAPI.model_validate(user_dict)

    def to_user_model(self) -> OptimizationParameters:
        return OptimizationParameters(
            simplex_range=self.simplex_optimization_range,
            transmission_capacities=self.transmission_capacities,
            include_constraints=self.binding_constraints,
            include_hurdlecosts=self.hurdle_costs,
            include_tc_minstablepower=self.thermal_clusters_min_stable_power,
            include_tc_min_ud_time=self.thermal_clusters_min_ud_time,
            include_dayahead=self.day_ahead_reserve,
            include_strategicreserve=self.strategic_reserve,
            include_spinningreserve=self.spinning_reserve,
            include_primaryreserve=self.primary_reserve,
            include_exportmps=self.export_mps,
            include_exportstructure=self.include_exportstructure,
            include_unfeasible_problem_behavior=self.unfeasible_problem_behavior,
        )


def parse_optimization_parameters_api(data: Any) -> OptimizationParameters:
    return OptimizationParametersAPI.model_validate(data).to_user_model()


def serialize_optimization_parameters_api(parameters: OptimizationParameters) -> dict[str, Any]:
    optimization_api_model = OptimizationParametersAPI.from_user_model(parameters)
    body = optimization_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
    if "includeExportstructure" in body:
        raise APIError("AntaresWeb doesn't support editing the parameter include_exportstructure")
    return body


@all_optional_model
class ThematicTrimmingParametersAPI(APIBaseModel):
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
    npcap_hours: bool
    bc_marg_cost: bool
    # Since v9.2
    sts_by_group: bool
    # Since v9.3
    dispatch_gen: bool
    renewable_gen: bool

    @staticmethod
    def from_user_model(user_class: ThematicTrimmingParameters) -> "ThematicTrimmingParametersAPI":
        user_dict = asdict(user_class)
        return ThematicTrimmingParametersAPI.model_validate(user_dict)

    def to_user_model(self) -> ThematicTrimmingParameters:
        return ThematicTrimmingParameters(
            ov_cost=self.ov_cost,
            op_cost=self.op_cost,
            mrg_price=self.mrg_price,
            co2_emis=self.co2_emis,
            dtg_by_plant=self.dtg_by_plant,
            balance=self.balance,
            row_bal=self.row_bal,
            psp=self.psp,
            misc_ndg=self.misc_ndg,
            load=self.load,
            h_ror=self.h_ror,
            wind=self.wind,
            solar=self.solar,
            nuclear=self.nuclear,
            lignite=self.lignite,
            coal=self.coal,
            gas=self.gas,
            oil=self.oil,
            mix_fuel=self.mix_fuel,
            misc_dtg=self.misc_dtg,
            h_stor=self.h_stor,
            h_pump=self.h_pump,
            h_lev=self.h_lev,
            h_infl=self.h_infl,
            h_ovfl=self.h_ovfl,
            h_val=self.h_val,
            h_cost=self.h_cost,
            unsp_enrg=self.unsp_enrg,
            spil_enrg=self.spil_enrg,
            lold=self.lold,
            lolp=self.lolp,
            avl_dtg=self.avl_dtg,
            dtg_mrg=self.dtg_mrg,
            max_mrg=self.max_mrg,
            np_cost=self.np_cost,
            np_cost_by_plant=self.np_cost_by_plant,
            nodu=self.nodu,
            nodu_by_plant=self.nodu_by_plant,
            flow_lin=self.flow_lin,
            ucap_lin=self.ucap_lin,
            loop_flow=self.loop_flow,
            flow_quad=self.flow_quad,
            cong_fee_alg=self.cong_fee_alg,
            cong_fee_abs=self.cong_fee_abs,
            marg_cost=self.marg_cost,
            cong_prob_plus=self.cong_prob_plus,
            cong_prob_minus=self.cong_prob_minus,
            hurdle_cost=self.hurdle_cost,
            res_generation_by_plant=self.res_generation_by_plant,
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
            dens=self.dens,
            profit_by_plant=self.profit_by_plant,
            sts_inj_by_plant=self.sts_inj_by_plant,
            sts_withdrawal_by_plant=self.sts_withdrawal_by_plant,
            sts_lvl_by_plant=self.sts_lvl_by_plant,
            sts_cashflow_by_cluster=self.sts_cashflow_by_cluster,
            npcap_hours=self.npcap_hours,
            bc_marg_cost=self.bc_marg_cost,
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
