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

from enum import Enum
from typing import Any, Optional

from antares.craft.model.settings.general import OutputChoices
from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, ConfigDict, Field, model_validator
from pydantic.alias_generators import to_camel
from typing_extensions import Self


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


class ReserveManagement(Enum):
    GLOBAL = "global"


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


class DefaultAdvancedParameters(BaseModel, alias_generator=to_camel):
    model_config = ConfigDict(use_enum_values=True)

    # Advanced parameters
    accuracy_on_correlation: Optional[set[OutputChoices]] = None
    # Other preferences
    initial_reservoir_levels: InitialReservoirLevel = Field(
        default=InitialReservoirLevel.COLD_START, validate_default=True
    )
    hydro_heuristic_policy: HydroHeuristicPolicy = Field(
        default=HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES, validate_default=True
    )
    hydro_pricing_mode: HydroPricingMode = Field(default=HydroPricingMode.FAST, validate_default=True)
    power_fluctuations: PowerFluctuation = Field(default=PowerFluctuation.FREE_MODULATIONS, validate_default=True)
    shedding_policy: SheddingPolicy = Field(default=SheddingPolicy.SHAVE_PEAKS, validate_default=True)
    unit_commitment_mode: UnitCommitmentMode = Field(default=UnitCommitmentMode.FAST, validate_default=True)
    number_of_cores_mode: SimulationCore = Field(default=SimulationCore.MEDIUM, validate_default=True)
    renewable_generation_modelling: RenewableGenerationModeling = Field(
        default=RenewableGenerationModeling.AGGREGATED, validate_default=True
    )
    # Seeds
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
class AdvancedParameters(DefaultAdvancedParameters):
    @model_validator(mode="before")
    def change_accuracy_on_correlation(cls, data: Any) -> Self:
        if "accuracyOnCorrelation" in data.keys():
            data["accuracyOnCorrelation"] = (
                {OutputChoices(list_item) for list_item in data["accuracyOnCorrelation"].replace(" ", "").split(",")}
                if data["accuracyOnCorrelation"]
                else None
            )
        return data


class AdvancedParametersLocal(DefaultAdvancedParameters, alias_generator=to_kebab):
    @property
    def ini_fields(self) -> dict:
        return {
            "other preferences": {
                "initial-reservoir-levels": self.initial_reservoir_levels,
                "hydro-heuristic-policy": self.hydro_heuristic_policy,
                "hydro-pricing-mode": self.hydro_pricing_mode,
                "power-fluctuations": self.power_fluctuations,
                "shedding-policy": self.shedding_policy,
                "unit-commitment-mode": self.unit_commitment_mode,
                "number-of-cores-mode": self.number_of_cores_mode,
                "renewable-generation-modelling": self.renewable_generation_modelling,
            },
            "advanced parameters": {
                "accuracy-on-correlation": self.accuracy_on_correlation if self.accuracy_on_correlation else "",
            },
            "seeds - Mersenne Twister": {
                "seed-tsgen-wind": str(self.seed_tsgen_wind),
                "seed-tsgen-load": str(self.seed_tsgen_load),
                "seed-tsgen-hydro": str(self.seed_tsgen_hydro),
                "seed-tsgen-thermal": str(self.seed_tsgen_thermal),
                "seed-tsgen-solar": str(self.seed_tsgen_solar),
                "seed-tsnumbers": str(self.seed_tsnumbers),
                "seed-unsupplied-energy-costs": str(self.seed_unsupplied_energy_costs),
                "seed-spilled-energy-costs": str(self.seed_spilled_energy_costs),
                "seed-thermal-costs": str(self.seed_thermal_costs),
                "seed-hydro-costs": str(self.seed_hydro_costs),
                "seed-initial-reservoir-levels": str(self.seed_initial_reservoir_levels),
            },
        }
