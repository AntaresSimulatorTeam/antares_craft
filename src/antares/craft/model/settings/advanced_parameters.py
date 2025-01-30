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
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional

from antares.craft.model.settings.general import OutputChoices
from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, Field


class InitialReservoirLevel(Enum):
    COLD_START = "cold start"
    HOT_START = "hot start"


class HydroHeuristicPolicy(Enum):
    ACCOMMODATE_RULES_CURVES = "accommodate rule curves"
    MAXIMIZE_GENERATION = "maximize generation"


class HydroPricingMode(Enum):
    FAST = "fast"
    ACCURATE = "accurate"


class PowerFluctuation(Enum):
    FREE_MODULATIONS = "free modulations"
    MINIMIZE_EXCURSIONS = "minimize excursions"
    MINIMIZE_RAMPING = "minimize ramping"


class SheddingPolicy(Enum):
    SHAVE_PEAKS = "shave peaks"
    MINIMIZE_DURATION = "minimize duration"


class UnitCommitmentMode(Enum):
    FAST = "fast"
    ACCURATE = "accurate"
    MILP = "milp"


class SimulationCore(Enum):
    MINIMUM = "minimum"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class RenewableGenerationModeling(Enum):
    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"


@dataclass
class AdvancedParameters:
    initial_reservoir_levels: Optional[InitialReservoirLevel] = None
    hydro_heuristic_policy: Optional[HydroHeuristicPolicy] = None
    hydro_pricing_mode: Optional[HydroPricingMode] = None
    power_fluctuations: Optional[PowerFluctuation] = None
    shedding_policy: Optional[SheddingPolicy] = None
    unit_commitment_mode: Optional[UnitCommitmentMode] = None
    number_of_cores_mode: Optional[SimulationCore] = None
    renewable_generation_modelling: Optional[RenewableGenerationModeling] = None
    accuracy_on_correlation: Optional[set[OutputChoices]] = None


@dataclass
class SeedParameters:
    seed_ts_gen_thermal: Optional[int] = None
    seed_ts_numbers: Optional[int] = None
    seed_unsupplied_energy_costs: Optional[int] = None
    seed_spilled_energy_costs: Optional[int] = None
    seed_thermal_costs: Optional[int] = None
    seed_hydro_costs: Optional[int] = None
    seed_initial_reservoir_levels: Optional[int] = None


@all_optional_model
class AdvancedAndSeedParametersAPI(BaseModel):
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


class AdvancedAndSeedParametersLocalEdition(BaseModel):
    other_preferences: OtherPreferencesLocalEdition = Field(default=None, alias="other preferences")
    advanced_parameters: AdvancedParametersLocalEdition = Field(default_factory=None, alias="advanced parameters")
    seeds: SeedParametersLocalEdition = Field(default_factory=None, alias="seeds - Mersenne Twister")
