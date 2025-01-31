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
from typing import Optional

from antares.craft.model.settings.general import OutputChoices


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
    seed_tsgen_thermal: Optional[int] = None
    seed_ts_numbers: Optional[int] = None
    seed_unsupplied_energy_costs: Optional[int] = None
    seed_spilled_energy_costs: Optional[int] = None
    seed_thermal_costs: Optional[int] = None
    seed_hydro_costs: Optional[int] = None
    seed_initial_reservoir_levels: Optional[int] = None
