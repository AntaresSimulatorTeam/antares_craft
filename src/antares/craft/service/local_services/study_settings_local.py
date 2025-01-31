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
from pathlib import Path
from typing import Any, Set

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
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from pydantic import BaseModel, Field


class AdequacyPatchParametersLocalCreation(BaseModel, alias_generator=to_kebab):
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
    def from_user_model(user_class: AdequacyPatchParameters) -> "AdequacyPatchParametersLocalCreation":
        user_dict = asdict(user_class)
        return AdequacyPatchParametersLocalCreation.model_validate(user_dict)

    def to_user_model(self) -> AdequacyPatchParameters:
        local_dict = self.model_dump(mode="json", by_alias=False, exclude={"enable_first_step"})
        return AdequacyPatchParameters(**local_dict)


@all_optional_model
class AdequacyPatchParametersLocalEdition(AdequacyPatchParametersLocalCreation):
    pass


class OtherPreferencesLocalCreation(BaseModel, alias_generator=to_kebab):
    initial_reservoir_levels: InitialReservoirLevel
    hydro_heuristic_policy: HydroHeuristicPolicy
    hydro_pricing_mode: HydroPricingMode
    power_fluctuations: PowerFluctuation
    shedding_policy: SheddingPolicy
    shedding_strategy: Any
    unit_commitment_mode: UnitCommitmentMode
    number_of_cores_mode: SimulationCore
    renewable_generation_modelling: RenewableGenerationModeling
    day_ahead_reserve_management: Any


@all_optional_model
class OtherPreferencesLocalEdition(OtherPreferencesLocalCreation):
    pass


class AdvancedParametersLocalCreation(BaseModel, alias_generator=to_kebab):
    accuracy_on_correlation: set[OutputChoices] = set()
    adequacy_block_size: int = 100


@all_optional_model
class AdvancedParametersLocalEdition(AdvancedParametersLocalCreation):
    pass


class SeedParametersLocalCreation(BaseModel, alias_generator=to_kebab):
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


@all_optional_model
class SeedParametersLocalEdition(SeedParametersLocalCreation):
    pass


class AdvancedAndSeedParametersLocalCreation(BaseModel):
    other_preferences: OtherPreferencesLocalCreation = Field(alias="other preferences")
    advanced_parameters: AdvancedParametersLocalCreation = Field(alias="advanced parameters")
    seeds: SeedParametersLocalCreation = Field(alias="seeds - Mersenne Twister")

    @staticmethod
    def from_user_model(
        advanced_parameters: AdvancedParameters, seed_parameters: SeedParameters
    ) -> "AdvancedAndSeedParametersLocalCreation":
        other_preferences_local_dict = asdict(advanced_parameters)
        advanced_local_dict = {
            "advanced_parameters": {
                "accuracy_on_correlation": other_preferences_local_dict.pop("accuracy_on_correlation")
            }
        }
        seed_local_dict = {"seeds": asdict(seed_parameters)}

        local_dict = {"other_preferences": other_preferences_local_dict} | advanced_local_dict | seed_local_dict

        return AdvancedAndSeedParametersLocalCreation.model_validate(local_dict)

    def to_seed_parameters_model(self) -> SeedParameters:
        seed_values = self.model_dump(mode="json", by_alias=False, include=set(asdict(SeedParameters()).keys()))
        return SeedParameters(**seed_values)

    def to_advanced_parameters_model(self) -> AdvancedParameters:
        advanced_values = self.model_dump(mode="json", by_alias=False, include=set(asdict(AdvancedParameters()).keys()))
        return AdvancedParameters(**advanced_values)


class AdvancedAndSeedParametersLocalEdition(AdvancedAndSeedParametersLocalCreation):
    other_preferences: OtherPreferencesLocalEdition = Field(default=None, alias="other preferences")
    advanced_parameters: AdvancedParametersLocalEdition = Field(default_factory=None, alias="advanced parameters")
    seeds: SeedParametersLocalEdition = Field(default_factory=None, alias="seeds - Mersenne Twister")


class GeneralSectionLocal(BaseModel):
    mode: Mode = Field(default=Mode.ECONOMY, validate_default=True)
    horizon: str = ""
    nb_years: int = Field(default=1, alias="nb.years")
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
    intra_model: bool = Field(default=False, alias="intra-model")
    inter_model: bool = Field(default=False, alias="inter-model")
    refresh_interval_load: int = Field(default=100, alias="refreshintervalload")
    refresh_interval_hydro: int = Field(default=100, alias="refreshintervalhydro")
    refresh_interval_wind: int = Field(default=100, alias="refreshintervalwind")
    refresh_interval_thermal: int = Field(default=100, alias="refreshintervalthermal")
    refresh_interval_solar: int = Field(default=100, alias="refreshintervalsolar")
    read_only: bool = Field(default=False, alias="readonly")


class OutputSectionLocal(BaseModel):
    synthesis: bool = True
    store_new_set: bool = Field(default=True, alias="storenewset")
    archives: set[OutputChoices] = set()


class GeneralParametersLocalCreation(BaseModel):
    general: GeneralSectionLocal
    input: dict = {"import": ""}
    output: OutputSectionLocal

    @staticmethod
    def from_user_model(user_class: GeneralParameters) -> "GeneralParametersLocalCreation":
        user_dict = asdict(user_class)

        output_dict = {
            "output": {
                "store_new_set": user_dict.pop("store_new_set"),
                "synthesis": user_dict.pop("simulation_synthesis"),
            }
        }
        general_dict = {"general": user_dict}
        local_dict = general_dict | output_dict

        return GeneralParametersLocalCreation.model_validate(local_dict)

    @staticmethod
    def get_excluded_fields_for_user_class() -> Set[str]:
        return {
            "generate",
            "nb_timeseries_load",
            "nb_timeseries_hydro",
            "nb_timeseries_wind",
            "nb_timeseries_solar",
            "refresh_timeseries",
            "intra_model",
            "inter_model",
            "refresh_interval_load",
            "refresh_interval_hydro",
            "refresh_interval_wind",
            "refresh_interval_thermal",
            "refresh_interval_solar",
            "read_only",
        }

    def to_user_model(self) -> GeneralParameters:
        local_dict = self.model_dump(mode="json", by_alias=False, exclude=self.get_excluded_fields_for_user_class())
        return GeneralParameters(**local_dict)


@all_optional_model
class GeneralParametersLocalEdition(GeneralParametersLocalCreation):
    pass


class OptimizationParametersLocalCreation(BaseModel, alias_generator=to_kebab):
    simplex_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK
    transmission_capacities: OptimizationTransmissionCapacities = OptimizationTransmissionCapacities.LOCAL_VALUES
    include_constraints: bool = True
    include_hurdle_costs: bool = True
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
    def from_user_model(user_class: OptimizationParameters) -> "OptimizationParametersLocalCreation":
        user_dict = asdict(user_class)
        return OptimizationParametersLocalCreation.model_validate(user_dict)

    def to_user_model(self) -> OptimizationParameters:
        local_dict = self.model_dump(mode="json", by_alias=False)
        return OptimizationParameters(**local_dict)


@all_optional_model
class OptimizationSettingsLocalEdition(OptimizationParametersLocalCreation):
    pass


def read_study_settings(study_directory: Path) -> StudySettings:
    general_data_ini = IniFile(study_directory, InitializationFilesTypes.THERMAL_AREAS_INI)
    ini_content = general_data_ini.ini_dict

    # general
    general_params_ini = {"general": ini_content["general"]}
    if general_params_ini.pop("derated", None):
        general_params_ini["building_mode"] = BuildingMode.DERATED.value
    if general_params_ini.pop("custom-scenario", None):
        general_params_ini["building_mode"] = BuildingMode.CUSTOM.value
    else:
        general_params_ini["building_mode"] = BuildingMode.AUTOMATIC.value

    excluded_keys = GeneralParametersLocalCreation.get_excluded_fields_for_user_class()
    for key in excluded_keys:
        general_params_ini.pop(key, None)

    output_parameters_ini = {"output": ini_content["output"]}
    local_general_ini = general_params_ini | output_parameters_ini
    general_parameters_local = GeneralParametersLocalCreation.model_validate(local_general_ini)
    general_parameters = general_parameters_local.to_user_model()

    # optimization
    optimization_ini = ini_content["optimization"]
    optimization_ini.pop("link-type", None)
    optimization_parameters_local = OptimizationParametersLocalCreation.model_validate(optimization_ini)
    optimization_parameters = optimization_parameters_local.to_user_model()

    # adequacy_patch
    adequacy_ini = ini_content["adequacy patch"]
    adequacy_parameters_local = AdequacyPatchParametersLocalCreation.model_validate(adequacy_ini)
    adequacy_patch_parameters = adequacy_parameters_local.to_user_model()

    # seed and advanced
    seed_local_parameters = SeedParametersLocalCreation.model_validate(ini_content["seeds - Mersenne Twister"])
    advanced_local_parameters = AdvancedParametersLocalCreation.model_validate(ini_content["advanced parameters"])
    other_preferences_local_parameters = OtherPreferencesLocalCreation.model_validate(ini_content["other preferences"])
    args = {
        "other_preferences": other_preferences_local_parameters,
        "seeds": seed_local_parameters,
        "advanced_parameters": advanced_local_parameters,
    }
    seed_and_advanced_local_parameters = AdvancedAndSeedParametersLocalCreation.model_validate(args)
    seed_parameters = seed_and_advanced_local_parameters.to_seed_parameters_model()
    advanced_parameters = seed_and_advanced_local_parameters.to_advanced_parameters_model()

    # playlist
    playlist_parameters = None
    if "playlist" in ini_content:
        playlist_parameters = None
        # todo

    # thematic trimming
    thematic_trimming_parameters = None
    if "variables selection" in ini_content:
        thematic_trimming_parameters = None
        # todo

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=playlist_parameters,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )


def edit_study_settings(study_directory: Path, settings: StudySettings) -> None:
    raise NotImplementedError
