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
from typing import Any, Sequence, Set, cast

from antares.craft.model.settings.adequacy_patch import AdequacyPatchParameters, PriceTakingOrder
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParameters,
    HydroHeuristicPolicy,
    HydroPricingMode,
    InitialReservoirLevel,
    PowerFluctuation,
    RenewableGenerationModeling,
    SeedParameters,
    SheddingPolicy,
    SimulationCore,
    UnitCommitmentMode,
)
from antares.craft.model.settings.general import BuildingMode, GeneralParameters, Mode, Month, OutputChoices, WeekDay
from antares.craft.model.settings.optimization import (
    OptimizationParameters,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.service.local_services.models import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab
from pydantic import Field, field_validator


class AdequacyPatchParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    include_adq_patch: bool = False
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: bool = True
    set_to_null_ntc_between_physical_out_for_first_step: bool = True
    price_taking_order: PriceTakingOrder = PriceTakingOrder.DENS
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 0
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 3
    enable_first_step: bool = False

    @staticmethod
    def from_user_model(user_class: AdequacyPatchParameters) -> "AdequacyPatchParametersLocal":
        user_dict = asdict(user_class)
        return AdequacyPatchParametersLocal.model_validate(user_dict)

    def to_user_model(self) -> AdequacyPatchParameters:
        local_dict = self.model_dump(mode="json", by_alias=False, exclude={"enable_first_step"})
        return AdequacyPatchParameters(**local_dict)


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
    def validate_accuracy_on_correlation(cls, v: Any) -> Sequence[str]:
        """Ensure the ID is lower case."""
        if v is None:
            return []
        return cast(Sequence[str], ast.literal_eval(v))


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
        advanced_parameters: AdvancedParameters, seed_parameters: SeedParameters
    ) -> "AdvancedAndSeedParametersLocal":
        other_preferences_local_dict = asdict(advanced_parameters)
        advanced_local_dict = {
            "advanced_parameters": {
                "accuracy_on_correlation": other_preferences_local_dict.pop("accuracy_on_correlation")
            }
        }
        seed_local_dict = {"seeds": asdict(seed_parameters)}

        local_dict = {"other_preferences": other_preferences_local_dict} | advanced_local_dict | seed_local_dict
        return AdvancedAndSeedParametersLocal.model_validate(local_dict)

    def to_seed_parameters_model(self) -> SeedParameters:
        seed_values = self.seeds.model_dump(mode="json", by_alias=False, include=set(asdict(SeedParameters()).keys()))
        return SeedParameters(**seed_values)

    def to_advanced_parameters_model(self) -> AdvancedParameters:
        includes = set(asdict(AdvancedParameters()).keys())
        advanced_values = self.advanced_parameters.model_dump(mode="json", by_alias=False, include=includes)
        other_preferences_values = self.other_preferences.model_dump(mode="json", by_alias=False, include=includes)
        merged_values = advanced_values | other_preferences_values
        return AdvancedParameters(**merged_values)


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
    def from_user_model(user_class: GeneralParameters) -> "GeneralParametersLocal":
        user_dict = asdict(user_class)

        output_dict = {
            "output": {
                "store_new_set": user_dict.pop("store_new_set"),
                "synthesis": user_dict.pop("simulation_synthesis"),
            }
        }
        general_dict = {"general": user_dict}
        local_dict = general_dict | output_dict

        return GeneralParametersLocal.model_validate(local_dict)

    @staticmethod
    def get_excluded_fields_for_user_class() -> Set[str]:
        return {
            "generate",
            "nb_timeseries_load",
            "nb_timeseries_hydro",
            "nb_timeseries_wind",
            "nb_timeseries_solar",
            "refresh_timeseries",
            "intra_modal",
            "inter_modal",
            "refresh_interval_load",
            "refresh_interval_hydro",
            "refresh_interval_wind",
            "refresh_interval_thermal",
            "refresh_interval_solar",
            "read_only",
        }

    def to_user_model(self) -> GeneralParameters:
        local_dict = self.general.model_dump(
            mode="json", by_alias=False, exclude=self.get_excluded_fields_for_user_class()
        )
        local_dict.update(self.output.model_dump(mode="json", by_alias=False, exclude={"archives"}))
        local_dict["simulation_synthesis"] = local_dict.pop("synthesis")
        return GeneralParameters(**local_dict)


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
    include_exportmps: bool = False
    include_exportstructure: bool = False
    include_unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE

    @staticmethod
    def from_user_model(user_class: OptimizationParameters) -> "OptimizationParametersLocal":
        user_dict = asdict(user_class)
        return OptimizationParametersLocal.model_validate(user_dict)

    def to_user_model(self) -> OptimizationParameters:
        local_dict = self.model_dump(mode="json", by_alias=False)
        return OptimizationParameters(**local_dict)
