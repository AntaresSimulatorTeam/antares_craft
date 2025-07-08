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
from typing import Any, Optional

from pydantic import Field, field_serializer, field_validator

from antares.craft.exceptions.exceptions import InvalidFieldForVersionError
from antares.craft.model.commons import join_with_comma
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
    OutputChoices,
)
from antares.craft.model.study import STUDY_VERSION_9_2
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.alias_generators import to_kebab
from antares.study.version import StudyVersion

AdvancedParametersType = AdvancedParameters | AdvancedParametersUpdate
SeedParametersType = SeedParameters | SeedParametersUpdate


class OtherPreferencesLocal(LocalBaseModel, alias_generator=to_kebab):
    hydro_heuristic_policy: HydroHeuristicPolicy = HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES
    hydro_pricing_mode: HydroPricingMode = HydroPricingMode.FAST
    power_fluctuations: PowerFluctuation = PowerFluctuation.FREE_MODULATIONS
    shedding_policy: SheddingPolicy = SheddingPolicy.SHAVE_PEAKS
    shedding_strategy: Any = "shave margins"
    unit_commitment_mode: UnitCommitmentMode = UnitCommitmentMode.FAST
    number_of_cores_mode: SimulationCore = SimulationCore.MEDIUM
    renewable_generation_modelling: RenewableGenerationModeling = RenewableGenerationModeling.CLUSTERS
    day_ahead_reserve_management: Any = "global"
    # Parameters removed since v9.2
    initial_reservoir_levels: Optional[InitialReservoirLevel] = None


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
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update, exclude_none=True)
        if update:
            for key in ["other preferences", "advanced parameters", "seeds - Mersenne Twister"]:
                if content[key]:
                    current_content[key].update(content[key])
        else:
            current_content.update(content)
        return current_content

    @staticmethod
    def get_9_2_removed_fields_and_default_value() -> dict[str, dict[str, Any]]:
        return {"other_preferences": {"initial_reservoir_levels": InitialReservoirLevel.COLD_START}}

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


def validate_against_version(parameters: AdvancedAndSeedParametersLocal, version: StudyVersion) -> None:
    if version >= STUDY_VERSION_9_2:
        for class_field, value in AdvancedAndSeedParametersLocal.get_9_2_removed_fields_and_default_value().items():
            for field in value:
                check_min_version(getattr(parameters, class_field), field, version)
    else:
        # We have to check if the used `shedding_policy` was available in the old version
        if parameters.other_preferences.shedding_policy == SheddingPolicy.ACCURATE_SHAVE_PEAKS:
            raise InvalidFieldForVersionError(
                f"Shedding policy should be `shave peaks` or `minimize duration` and was '{parameters.other_preferences.shedding_policy.value}'"
            )


def initialize_with_version(
    parameters: AdvancedAndSeedParametersLocal, version: StudyVersion
) -> AdvancedAndSeedParametersLocal:
    if version < STUDY_VERSION_9_2:
        for class_field, values in AdvancedAndSeedParametersLocal.get_9_2_removed_fields_and_default_value().items():
            for field, value in values.items():
                initialize_field_default(getattr(parameters, class_field), field, value)
    return parameters


def parse_advanced_and_seed_parameters_local(
    study_version: StudyVersion, data: Any
) -> tuple[AdvancedParameters, SeedParameters]:
    seed_local_parameters = SeedParametersLocal.model_validate(data.get("seeds - Mersenne Twister", {}))
    advanced_local_parameters = AdvancedParametersLocal.model_validate(data.get("advanced parameters", {}))
    other_preferences_local_parameters = OtherPreferencesLocal.model_validate(data.get("other preferences", {}))
    args = {
        "other_preferences": other_preferences_local_parameters,
        "seeds": seed_local_parameters,
        "advanced_parameters": advanced_local_parameters,
    }
    local_parameters = AdvancedAndSeedParametersLocal.model_validate(args)
    validate_against_version(local_parameters, study_version)
    initialize_with_version(local_parameters, study_version)
    return local_parameters.to_advanced_parameters_model(), local_parameters.to_seed_parameters_model()


def serialize_advanced_and_seed_parameters_local(
    parameters: tuple[AdvancedParametersType, SeedParametersType], study_version: StudyVersion
) -> AdvancedAndSeedParametersLocal:
    local_parameters = AdvancedAndSeedParametersLocal.from_user_model(parameters[0], parameters[1])
    validate_against_version(local_parameters, study_version)
    return local_parameters
