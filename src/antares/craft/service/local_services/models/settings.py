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
from dataclasses import asdict
from typing import Any, Set

from pydantic import Field, field_serializer, field_validator

from antares.craft import PlaylistParameters, ThematicTrimmingParameters
from antares.craft.model.commons import join_with_comma
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
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab

AdequacyPatchParametersType = AdequacyPatchParameters | AdequacyPatchParametersUpdate


class AdequacyPatchParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    include_adq_patch: bool = False
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: bool = True
    set_to_null_ntc_between_physical_out_for_first_step: bool = True
    price_taking_order: PriceTakingOrder = PriceTakingOrder.DENS
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 1
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 7
    enable_first_step: bool = False

    @staticmethod
    def from_user_model(user_class: AdequacyPatchParametersType) -> "AdequacyPatchParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return AdequacyPatchParametersLocal.model_validate(user_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        current_content.setdefault("adequacy patch", {}).update(content)
        return current_content

    def to_user_model(self) -> AdequacyPatchParameters:
        return AdequacyPatchParameters(
            include_adq_patch=self.include_adq_patch,
            set_to_null_ntc_from_physical_out_to_physical_in_for_first_step=self.set_to_null_ntc_from_physical_out_to_physical_in_for_first_step,
            set_to_null_ntc_between_physical_out_for_first_step=self.set_to_null_ntc_between_physical_out_for_first_step,
            price_taking_order=self.price_taking_order,
            include_hurdle_cost_csr=self.include_hurdle_cost_csr,
            check_csr_cost_function=self.check_csr_cost_function,
            threshold_initiate_curtailment_sharing_rule=self.threshold_initiate_curtailment_sharing_rule,
            threshold_display_local_matching_rule_violations=self.threshold_display_local_matching_rule_violations,
            threshold_csr_variable_bounds_relaxation=self.threshold_csr_variable_bounds_relaxation,
        )


AdvancedParametersType = AdvancedParameters | AdvancedParametersUpdate
SeedParametersType = SeedParameters | SeedParametersUpdate


class OtherPreferencesLocal(LocalBaseModel, alias_generator=to_kebab):
    initial_reservoir_levels: InitialReservoirLevel = InitialReservoirLevel.COLD_START
    hydro_heuristic_policy: HydroHeuristicPolicy = HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES
    hydro_pricing_mode: HydroPricingMode = HydroPricingMode.FAST
    power_fluctuations: PowerFluctuation = PowerFluctuation.FREE_MODULATIONS
    shedding_policy: SheddingPolicy = SheddingPolicy.SHAVE_PEAKS
    shedding_strategy: Any = "shave margins"
    unit_commitment_mode: UnitCommitmentMode = UnitCommitmentMode.FAST
    number_of_cores_mode: SimulationCore = SimulationCore.MEDIUM
    renewable_generation_modelling: RenewableGenerationModeling = RenewableGenerationModeling.CLUSTERS
    day_ahead_reserve_management: Any = "global"


class AdvancedParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    accuracy_on_correlation: set[OutputChoices] = set()
    adequacy_block_size: int = 100

    @field_validator("accuracy_on_correlation", mode="before")
    def validate_accuracy_on_correlation(cls, v: Any) -> set[Any]:
        if not v:
            return set()

        if isinstance(v, set):
            return v

        splitted_value = v.replace(" ", "").split(",")
        correlation = set()
        for choice in splitted_value:
            correlation.add(OutputChoices(choice))
        return correlation

    @field_serializer("accuracy_on_correlation")
    def serialize_accuracy_on_correlation(self, v: set[OutputChoices]) -> str:
        return join_with_comma(v)


class SeedParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    seed_tsgen_wind: int = 5489
    seed_tsgen_load: int = 1005489
    seed_tsgen_hydro: int = 2005489
    seed_tsgen_thermal: int = 3005489
    seed_tsgen_solar: int = 4005489
    seed_tsnumbers: int = 5005489
    seed_unsupplied_energy_costs: int = 6005489
    seed_spilled_energy_costs: int = 7005489
    seed_thermal_costs: int = 8005489
    seed_hydro_costs: int = 9005489
    seed_initial_reservoir_levels: int = 10005489


class AdvancedAndSeedParametersLocal(LocalBaseModel):
    other_preferences: OtherPreferencesLocal = Field(alias="other preferences")
    advanced_parameters: AdvancedParametersLocal = Field(alias="advanced parameters")
    seeds: SeedParametersLocal = Field(alias="seeds - Mersenne Twister")

    @staticmethod
    def from_user_model(
        advanced_parameters: AdvancedParametersType, seed_parameters: SeedParametersType
    ) -> "AdvancedAndSeedParametersLocal":
        other_preferences_local_dict = {k: v for k, v in asdict(advanced_parameters).items() if v is not None}

        advanced_local_dict: dict[str, dict[str, Any]] = {"advanced_parameters": {}}
        if advanced_parameters.accuracy_on_correlation is not None:
            advanced_local_dict["advanced_parameters"] = {
                "accuracy_on_correlation": other_preferences_local_dict.pop("accuracy_on_correlation")
            }

        seed_local_dict = {"seeds": {k: v for k, v in asdict(seed_parameters).items() if v is not None}}

        local_dict = {"other_preferences": other_preferences_local_dict} | advanced_local_dict | seed_local_dict
        return AdvancedAndSeedParametersLocal.model_validate(local_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        if update:
            for key in ["other preferences", "advanced parameters", "seeds - Mersenne Twister"]:
                if content[key]:
                    current_content[key].update(content[key])
        else:
            current_content.update(content)
        return current_content

    def to_seed_parameters_model(self) -> SeedParameters:
        return SeedParameters(
            seed_tsgen_thermal=self.seeds.seed_tsgen_thermal,
            seed_tsnumbers=self.seeds.seed_tsnumbers,
            seed_unsupplied_energy_costs=self.seeds.seed_unsupplied_energy_costs,
            seed_spilled_energy_costs=self.seeds.seed_spilled_energy_costs,
            seed_thermal_costs=self.seeds.seed_thermal_costs,
            seed_hydro_costs=self.seeds.seed_hydro_costs,
            seed_initial_reservoir_levels=self.seeds.seed_initial_reservoir_levels,
        )

    def to_advanced_parameters_model(self) -> AdvancedParameters:
        return AdvancedParameters(
            initial_reservoir_levels=self.other_preferences.initial_reservoir_levels,
            hydro_heuristic_policy=self.other_preferences.hydro_heuristic_policy,
            hydro_pricing_mode=self.other_preferences.hydro_pricing_mode,
            power_fluctuations=self.other_preferences.power_fluctuations,
            shedding_policy=self.other_preferences.shedding_policy,
            unit_commitment_mode=self.other_preferences.unit_commitment_mode,
            number_of_cores_mode=self.other_preferences.number_of_cores_mode,
            renewable_generation_modelling=self.other_preferences.renewable_generation_modelling,
            accuracy_on_correlation=self.advanced_parameters.accuracy_on_correlation,
        )


GeneralParametersType = GeneralParameters | GeneralParametersUpdate


class GeneralSectionLocal(LocalBaseModel):
    mode: Mode = Mode.ECONOMY
    horizon: str = ""
    nb_years: int = Field(default=1, alias="nbyears")
    simulation_start: int = Field(default=1, alias="simulation.start")
    simulation_end: int = Field(default=365, alias="simulation.end")
    january_first: WeekDay = Field(default=WeekDay.MONDAY, alias="january.1st")
    first_month_in_year: Month = Field(default=Month.JANUARY, alias="first-month-in-year")
    first_week_day: WeekDay = Field(default=WeekDay.MONDAY, alias="first.weekday")
    leap_year: bool = Field(default=False, alias="leapyear")
    year_by_year: bool = Field(default=False, alias="year-by-year")
    building_mode: BuildingMode = BuildingMode.AUTOMATIC
    user_playlist: bool = Field(default=False, alias="user-playlist")
    thematic_trimming: bool = Field(default=False, alias="thematic-trimming")
    geographic_trimming: bool = Field(default=False, alias="geographic-trimming")
    generate: bool = False
    nb_timeseries_load: int = Field(default=1, alias="nbtimeseriesload")
    nb_timeseries_hydro: int = Field(default=1, alias="nbtimeserieshydro")
    nb_timeseries_wind: int = Field(default=1, alias="nbtimeserieswind")
    nb_timeseries_thermal: int = Field(default=1, alias="nbtimeseriesthermal")
    nb_timeseries_solar: int = Field(default=1, alias="nbtimeseriessolar")
    refresh_timeseries: bool = Field(default=False, alias="refreshtimeseries")
    intra_modal: bool = Field(default=False, alias="intra-modal")
    inter_modal: bool = Field(default=False, alias="inter-modal")
    refresh_interval_load: int = Field(default=100, alias="refreshintervalload")
    refresh_interval_hydro: int = Field(default=100, alias="refreshintervalhydro")
    refresh_interval_wind: int = Field(default=100, alias="refreshintervalwind")
    refresh_interval_thermal: int = Field(default=100, alias="refreshintervalthermal")
    refresh_interval_solar: int = Field(default=100, alias="refreshintervalsolar")
    read_only: bool = Field(default=False, alias="readonly")


class OutputSectionLocal(LocalBaseModel):
    synthesis: bool = True
    store_new_set: bool = Field(default=False, alias="storenewset")
    archives: Any = ""


class GeneralParametersLocal(LocalBaseModel):
    general: GeneralSectionLocal
    input: dict[str, str] = {"import": ""}
    output: OutputSectionLocal

    @staticmethod
    def from_user_model(user_class: GeneralParametersType) -> "GeneralParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}

        output_dict = {}
        if user_class.store_new_set is not None:
            output_dict["store_new_set"] = user_dict.pop("store_new_set")
        if user_class.simulation_synthesis is not None:
            output_dict["synthesis"] = user_dict.pop("simulation_synthesis")

        general_dict = {"general": user_dict}
        local_dict = general_dict | {"output": output_dict}

        return GeneralParametersLocal.model_validate(local_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        if "building_mode" in content["general"]:
            general_values = content["general"]
            del general_values["building_mode"]
            building_mode = self.general.building_mode
            general_values["derated"] = building_mode == BuildingMode.DERATED
            general_values["custom-scenario"] = building_mode == BuildingMode.CUSTOM

        if update:
            for key in ["general", "output"]:
                if content[key]:
                    current_content[key].update(content[key])
        else:
            current_content.update(content)
        return current_content

    @staticmethod
    def get_excluded_fields_for_user_class() -> Set[str]:
        return {
            "generate",
            "nbtimeseriesload",
            "nbtimeserieshydro",
            "nbtimeserieswind",
            "nbtimeseriessolar",
            "refreshtimeseries",
            "intra-modal",
            "inter-modal",
            "refreshintervalload",
            "refreshintervalhydro",
            "refreshintervalwind",
            "refreshintervalthermal",
            "refreshintervalsolar",
            "readonly",
        }

    def to_user_model(self) -> GeneralParameters:
        return GeneralParameters(
            mode=self.general.mode,
            horizon=self.general.horizon,
            nb_years=self.general.nb_years,
            simulation_start=self.general.simulation_start,
            simulation_end=self.general.simulation_end,
            january_first=self.general.january_first,
            first_month_in_year=self.general.first_month_in_year,
            first_week_day=self.general.first_week_day,
            leap_year=self.general.leap_year,
            year_by_year=self.general.year_by_year,
            simulation_synthesis=self.output.synthesis,
            building_mode=self.general.building_mode,
            user_playlist=self.general.user_playlist,
            thematic_trimming=self.general.thematic_trimming,
            geographic_trimming=self.general.geographic_trimming,
            store_new_set=self.output.store_new_set,
            nb_timeseries_thermal=self.general.nb_timeseries_thermal,
        )


OptimizationParametersType = OptimizationParameters | OptimizationParametersUpdate


class OptimizationParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    simplex_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK
    transmission_capacities: OptimizationTransmissionCapacities = OptimizationTransmissionCapacities.LOCAL_VALUES
    include_constraints: bool = True
    include_hurdlecosts: bool = True
    include_tc_minstablepower: bool = True
    include_tc_min_ud_time: bool = True
    include_dayahead: bool = True
    include_strategicreserve: bool = True
    include_spinningreserve: bool = True
    include_primaryreserve: bool = True
    include_exportmps: ExportMPS = ExportMPS.FALSE
    include_exportstructure: bool = False
    include_unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE

    @field_validator("include_exportmps", mode="before")
    def validate_export_mps(cls, v: Any) -> Any:
        # `False` and `None` are the same for the simulator
        if isinstance(v, str) and v.lower() == "none":
            v = False
        return v

    @staticmethod
    def from_user_model(user_class: OptimizationParametersType) -> "OptimizationParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return OptimizationParametersLocal.model_validate(user_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        current_content.setdefault("optimization", {}).update(content)
        return current_content

    def to_user_model(self) -> OptimizationParameters:
        return OptimizationParameters(
            simplex_range=self.simplex_range,
            transmission_capacities=self.transmission_capacities,
            include_constraints=self.include_constraints,
            include_hurdlecosts=self.include_hurdlecosts,
            include_tc_minstablepower=self.include_tc_minstablepower,
            include_tc_min_ud_time=self.include_tc_min_ud_time,
            include_dayahead=self.include_dayahead,
            include_strategicreserve=self.include_strategicreserve,
            include_spinningreserve=self.include_spinningreserve,
            include_primaryreserve=self.include_primaryreserve,
            include_exportmps=self.include_exportmps,
            include_exportstructure=self.include_exportstructure,
            include_unfeasible_problem_behavior=self.include_unfeasible_problem_behavior,
        )


class PlaylistParametersLocal(LocalBaseModel):
    playlist_reset: bool
    playlist_plus: list[int] | None = Field(None, alias="playlist_year +")
    playlist_minus: list[int] | None = Field(None, alias="playlist_year -")
    playlist_year_weight: list[str] | None = None

    def to_user_model(self, nb_years: int) -> dict[int, PlaylistParameters]:
        playlist_dict: dict[int, PlaylistParameters] = {}

        # Builds the `weight` dict
        weight_dict: dict[int, float] = {}
        if self.playlist_year_weight:
            for weight_str in self.playlist_year_weight:
                year, weight = weight_str.split(",")
                weight_dict[int(year)] = float(weight)

        # Builds the `status` dict
        if self.playlist_reset:
            status_dict = dict.fromkeys(range(nb_years), True)
            if self.playlist_minus:
                for disabled_year in self.playlist_minus:
                    status_dict[disabled_year] = False
        else:
            status_dict = dict.fromkeys(range(nb_years), False)
            if self.playlist_plus:
                for enabled_year in self.playlist_plus:
                    status_dict[enabled_year] = True

        # Builds the user object
        for playlist_year in range(nb_years):
            playlist_weight = weight_dict.get(playlist_year, 1)
            # Change starting year from 0 to 1
            playlist_dict[playlist_year + 1] = PlaylistParameters(
                status=status_dict[playlist_year], weight=playlist_weight
            )

        return playlist_dict

    @staticmethod
    def create(user_class: dict[int, PlaylistParameters], nb_years: int) -> "PlaylistParametersLocal":
        playlist_year_weight = []
        playlist_plus = []
        playlist_minus = []
        # Fill the parameters
        for year, parameters in user_class.items():
            # Change starting year from 1 to 0
            local_year = year - 1
            if parameters.status:
                playlist_plus.append(local_year)
            else:
                playlist_minus.append(local_year)
            if parameters.weight != 1:
                playlist_year_weight.append(f"{local_year},{parameters.weight}")

        # Calculates what's the lighter to write
        args: dict[str, Any] = {"playlist_year_weight": playlist_year_weight}
        nb_years_activated = len(playlist_plus)
        nb_years_deactivated = len(playlist_minus)
        if nb_years_activated > nb_years_deactivated:
            playlist_reset = True
            args["playlist_plus"] = None
            if nb_years_deactivated == nb_years:
                playlist_minus = []
            args["playlist_minus"] = playlist_minus
        else:
            playlist_reset = False
            args["playlist_minus"] = None
            if nb_years_activated == nb_years:
                playlist_plus = []
            args["playlist_plus"] = playlist_plus

        args["playlist_reset"] = playlist_reset
        return PlaylistParametersLocal.model_validate(args)


class ThematicTrimmingParametersLocal(LocalBaseModel):
    ov_cost: bool | None = Field(default=None, alias="OV. COST")
    op_cost: bool | None = Field(default=None, alias="OP. COST")
    mrg_price: bool | None = Field(default=None, alias="MRG. PRICE")
    co2_emis: bool | None = Field(default=None, alias="CO2 EMIS.")
    dtg_by_plant: bool | None = Field(default=None, alias="DTG by plant")
    balance: bool | None = Field(default=None, alias="BALANCE")
    row_bal: bool | None = Field(default=None, alias="ROW BAL.")
    psp: bool | None = Field(default=None, alias="PSP")
    misc_ndg: bool | None = Field(default=None, alias="MISC. NDG")
    load: bool | None = Field(default=None, alias="LOAD")
    h_ror: bool | None = Field(default=None, alias="H. ROR")
    wind: bool | None = Field(default=None, alias="WIND")
    solar: bool | None = Field(default=None, alias="SOLAR")
    nuclear: bool | None = Field(default=None, alias="NUCLEAR")
    lignite: bool | None = Field(default=None, alias="LIGNITE")
    coal: bool | None = Field(default=None, alias="COAL")
    gas: bool | None = Field(default=None, alias="GAS")
    oil: bool | None = Field(default=None, alias="OIL")
    mix_fuel: bool | None = Field(default=None, alias="MIX. FUEL")
    misc_dtg: bool | None = Field(default=None, alias="MISC. DTG")
    h_stor: bool | None = Field(default=None, alias="H. STOR")
    h_pump: bool | None = Field(default=None, alias="H. PUMP")
    h_lev: bool | None = Field(default=None, alias="H. LEV")
    h_infl: bool | None = Field(default=None, alias="H. INFL")
    h_ovfl: bool | None = Field(default=None, alias="H. OVFL")
    h_val: bool | None = Field(default=None, alias="H. VAL")
    h_cost: bool | None = Field(default=None, alias="H. COST")
    unsp_enrg: bool | None = Field(default=None, alias="UNSP. ENRG")
    spil_enrg: bool | None = Field(default=None, alias="SPIL. ENRG")
    lold: bool | None = Field(default=None, alias="LOLD")
    lolp: bool | None = Field(default=None, alias="LOLP")
    avl_dtg: bool | None = Field(default=None, alias="AVL DTG")
    dtg_mrg: bool | None = Field(default=None, alias="DTG MRG")
    max_mrg: bool | None = Field(default=None, alias="MAX MRG")
    np_cost: bool | None = Field(default=None, alias="NP COST")
    np_cost_by_plant: bool | None = Field(default=None, alias="NP Cost by plant")
    nodu: bool | None = Field(default=None, alias="NODU")
    nodu_by_plant: bool | None = Field(default=None, alias="NODU by plant")
    flow_lin: bool | None = Field(default=None, alias="FLOW LIN.")
    ucap_lin: bool | None = Field(default=None, alias="UCAP LIN.")
    loop_flow: bool | None = Field(default=None, alias="LOOP FLOW")
    flow_quad: bool | None = Field(default=None, alias="FLOW QUAD.")
    cong_fee_alg: bool | None = Field(default=None, alias="CONG. FEE (ALG.)")
    cong_fee_abs: bool | None = Field(default=None, alias="CONG. FEE (ABS.)")
    marg_cost: bool | None = Field(default=None, alias="MARG. COST")
    cong_prob_plus: bool | None = Field(default=None, alias="CONG. PROB +")
    cong_prob_minus: bool | None = Field(default=None, alias="CONG. PROB -")
    hurdle_cost: bool | None = Field(default=None, alias="HURDLE COST")
    # since v8.1
    res_generation_by_plant: bool | None = Field(default=None, alias="RES generation by plant")
    misc_dtg_2: bool | None = Field(default=None, alias="MISC. DTG 2")
    misc_dtg_3: bool | None = Field(default=None, alias="MISC. DTG 3")
    misc_dtg_4: bool | None = Field(default=None, alias="MISC. DTG 4")
    wind_offshore: bool | None = Field(default=None, alias="WIND OFFSHORE")
    wind_onshore: bool | None = Field(default=None, alias="WIND ONSHORE")
    solar_concrt: bool | None = Field(default=None, alias="SOLAR CONCR")
    solar_pv: bool | None = Field(default=None, alias="SOLAR PV")
    solar_rooft: bool | None = Field(default=None, alias="SOLAR ROOFT")
    renw_1: bool | None = Field(default=None, alias="RENW. 1")
    renw_2: bool | None = Field(default=None, alias="RENW. 2")
    renw_3: bool | None = Field(default=None, alias="RENW. 3")
    renw_4: bool | None = Field(default=None, alias="RENW. 4")
    # since v8.3
    dens: bool | None = Field(default=None, alias="DENS")
    profit_by_plant: bool | None = Field(default=None, alias="Profit by plant")
    # since v8.6
    sts_inj_by_plant: bool | None = Field(default=None, alias="STS inj by plant")
    sts_withdrawal_by_plant: bool | None = Field(default=None, alias="STS withdrawal by plant")
    sts_lvl_by_plant: bool | None = Field(default=None, alias="STS lvl by plant")
    psp_open_injection: bool | None = Field(default=None, alias="PSP_open_injection")
    psp_open_withdrawal: bool | None = Field(default=None, alias="PSP_open_withdrawal")
    psp_open_level: bool | None = Field(default=None, alias="PSP_open_level")
    psp_closed_injection: bool | None = Field(default=None, alias="PSP_closed_injection")
    psp_closed_withdrawal: bool | None = Field(default=None, alias="PSP_closed_withdrawal")
    psp_closed_level: bool | None = Field(default=None, alias="PSP_closed_level")
    pondage_injection: bool | None = Field(default=None, alias="Pondage_injection")
    pondage_withdrawal: bool | None = Field(default=None, alias="Pondage_withdrawal")
    pondage_level: bool | None = Field(default=None, alias="Pondage_level")
    battery_injection: bool | None = Field(default=None, alias="Battery_injection")
    battery_withdrawal: bool | None = Field(default=None, alias="Battery_withdrawal")
    battery_level: bool | None = Field(default=None, alias="Battery_level")
    other1_injection: bool | None = Field(default=None, alias="Other1_injection")
    other1_withdrawal: bool | None = Field(default=None, alias="Other1_withdrawal")
    other1_level: bool | None = Field(default=None, alias="Other1_level")
    other2_injection: bool | None = Field(default=None, alias="Other2_injection")
    other2_withdrawal: bool | None = Field(default=None, alias="Other2_withdrawal")
    other2_level: bool | None = Field(default=None, alias="Other2_level")
    other3_injection: bool | None = Field(default=None, alias="Other3_injection")
    other3_withdrawal: bool | None = Field(default=None, alias="Other3_withdrawal")
    other3_level: bool | None = Field(default=None, alias="Other3_level")
    other4_injection: bool | None = Field(default=None, alias="Other4_injection")
    other4_withdrawal: bool | None = Field(default=None, alias="Other4_withdrawal")
    other4_level: bool | None = Field(default=None, alias="Other4_level")
    other5_injection: bool | None = Field(default=None, alias="Other5_injection")
    other5_withdrawal: bool | None = Field(default=None, alias="Other5_withdrawal")
    other5_level: bool | None = Field(default=None, alias="Other5_level")
    # Since v8.8
    sts_cashflow_by_cluster: bool | None = Field(default=None, alias="STS Cashflow By Cluster")

    def to_user_model(self) -> ThematicTrimmingParameters:
        return ThematicTrimmingParameters(**self.model_dump(exclude_none=True))

    @staticmethod
    def from_user_model(user_class: ThematicTrimmingParameters) -> "ThematicTrimmingParametersLocal":
        return ThematicTrimmingParametersLocal(**asdict(user_class))

    def to_ini(self) -> dict[str, Any]:
        data = self.model_dump(by_alias=True)
        content_plus = []
        content_minus = []
        for key, value in data.items():
            if value:
                content_plus.append(key)
            else:
                content_minus.append(key)
        if len(content_minus) >= len(content_plus):
            ini_content: dict[str, Any] = {"selected_vars_reset": False}
            if content_plus:
                ini_content["select_var +"] = content_plus
        else:
            ini_content = {"selected_vars_reset": True}
            if content_minus:
                ini_content["select_var -"] = content_minus
        return ini_content

    @staticmethod
    def from_ini(content: dict[str, Any]) -> "ThematicTrimmingParametersLocal":
        if content.get("selected_vars_reset", True):
            # Means written fields are deactivated and others are activated
            unselected_vars = content.get("select_var -", [])
            args = dict.fromkeys(unselected_vars, False)
            return ThematicTrimmingParametersLocal(**args)

        # Means written fields are activated and others deactivated
        selected_vars = content.get("select_var +", [])
        args = dict.fromkeys(selected_vars, True)
        file_data = ThematicTrimmingParametersLocal(**args)
        # Initialize missing fields
        for field in ThematicTrimmingParametersLocal.model_fields:
            if getattr(file_data, field) is None:
                setattr(file_data, field, False)
        return file_data
