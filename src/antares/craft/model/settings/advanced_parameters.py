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
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional

from antares.craft.model.settings.general import OutputChoices


class InitialReservoirLevel(Enum):
    """Initial reservoir level.

    Note that the reservoir level is now always determined with cold start behaviour since v9.2.
    TODO: put link to doc, currently https://antares-simulator.readthedocs.io/en/stable/user-guide/solver/09-appendix/#details-on-the-initial-reservoir-levels-parameter-deprecated-since-92
    
    Attributes:
        COLD_START: On starting the simulation of a new Monte-Carlo year, 
            the reservoir level to consider in each Area on the first day of the initialization month is randomly drawn 
            between the extreme levels defined for the Area on that day.
        HOT_START: On starting the simulation of a new Monte-Carlo year, 
            the reservoir level to consider in each Area on the first day of the initialization month is set to the value reached 
            at the end of the previous simulated year (see the conditions [here](https://antares-simulator.readthedocs.io/en/stable/user-guide/solver/09-appendix/#details-on-the-initial-reservoir-levels-parameter-deprecated-since-92))
    """
    COLD_START = "cold start"
    HOT_START = "hot start"


class HydroHeuristicPolicy(Enum):
    """Heuristic policy of hydro.

    This parameter is meant to define how the reservoir level should be managed throughout the year, 
    either with emphasis put on the respect of rule curves or on the maximization of the use of natural inflows.

    
    Attributes:
        ACCOMMODATE_RULES_CURVES: Upper and lower rule curves are accommodated in both monthly and daily heuristic stages.
            In the second stage, violations of the lower rule curve are avoided as much as possible 
            (penalty cost on $\\Psi$ higher than penalty cost on $Y$). 
            This policy may result in a restriction of the overall yearly energy generated from the natural inflows.
        MAXIMIZE_GENERATION: Upper and lower rule curves are accommodated in both monthly and daily heuristic stages. 
            In the second stage, incomplete use of natural inflows is avoided as much as possible 
            (penalty cost on $Y$ higher than penalty cost on $\\Psi$). This policy may result in violations of the lower rule curve.
    """
    ACCOMMODATE_RULES_CURVES = "accommodate rule curves"
    MAXIMIZE_GENERATION = "maximize generation"


class HydroPricingMode(Enum):
    """Hydro pricing mode.
    
    This parameter is meant to define how the reservoir level difference between the beginning 
    and the end of an optimization week should be reflected in the hydro economic signal (water value) used 
    in the computation of optimal hourly generated /pumped power during this week.

    Attributes:
        FAST: The water value is taken to remain about the same throughout the week, 
            and a constant value equal to that found at the date and for the level at which the week begins 
            is used in the course of the optimization. A value interpolated from the reference table for the exact level reached at each time step within the week is used ex-post in the assessment of the variable "H.COST" (positive for generation, negative for pumping).
            This option should be reserved to simulations in which computation resources are an issue 
            or to simulations in which level-dependent water value variations throughout a week are known to be small.
        ACCURATE: The water value is considered as variable throughout the week. As a consequence, 
            a different cost is used for each "layer" of the stock from/to which energy can be withdrawn/injected, 
            in an internal hydro merit-order involving the 100 tabulated water-values found at the date at which the week ends. 
            A value interpolated from the reference table for the exact level reached at each time step within the week is used ex-post in the assessment of the variable "H.COST" (positive for generation, negative for pumping). 
            This option should be used if computation resources are not an issue
            and if level-dependent water value variations throughout a week must be accounted for.

    """
    FAST = "fast"
    ACCURATE = "accurate"


class PowerFluctuation(Enum):
    """Power fluctuations.

    Attributes:
        FREE_MODULATIONS:
        MINIMIZE_EXCURSIONS:
        MINIMIZE_RAMPING:
    """
    FREE_MODULATIONS = "free modulations"
    MINIMIZE_EXCURSIONS = "minimize excursions"
    MINIMIZE_RAMPING = "minimize ramping"


class SheddingPolicy(Enum):
    """Shedding policy.
    
    Attributes:
        SHAVE_PEAKS:
        MINIMIZE_DURATION:
        ACCURATE_SHAVE_PEAKS: *Introduced in v9.2 of Antares Simulator.*
    """

    SHAVE_PEAKS = "shave peaks"
    MINIMIZE_DURATION = "minimize duration"
    # Introduced in v9.2
    ACCURATE_SHAVE_PEAKS = "accurate shave peaks"


class UnitCommitmentMode(Enum):
    """Unit commitment mode.

    TODO: link to a diagram of the different modes
    TODO: link to https://antares-simulator.readthedocs.io/en/stable/user-guide/solver/09-appendix/#details-on-the-unit-commitment-mode-parameter
    
    Attributes:
        FAST: Heuristic in which 2 LP (Linear Programming) problems are solved. No explicit modelling for the number of ON/OFF units.
        ACCURATE: Heuristic in which 2 LP (Linear Programming) problems are solved. Explicit modelling for the number of ON/OFF units. Slower than `fast`.
        MILP: A single MILP  (Mixed Integer Linear Program) problem is solved, with explicit modelling for the number of ON/OFF units. Slower than accurate
    """
    FAST = "fast"
    ACCURATE = "accurate"
    MILP = "milp"


class SimulationCore(Enum):
    """Simulation core.

    Useful to select multi-threading option.
    TODO: https://antares-simulator.readthedocs.io/en/stable/user-guide/solver/optional-features/multi-threading/

    Attributes:
        MINIMUM:
        LOW:
        MEDIUM:
        HIGH:
        MAXIMUM:
    """
    MINIMUM = "minimum"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    MAXIMUM = "maximum"


class RenewableGenerationModeling(Enum):
    """Renewable generation modelling.
    
    Attributes:
        AGGREGATED: *Deprecated since v8.1*
        CLUSTERS: 
    """
    AGGREGATED = "aggregated"
    CLUSTERS = "clusters"


@dataclass(frozen=True)
class AdvancedParameters:
    """Advanced parameters.
    
    Attributes:
        hydro_heuristic_policy: Choice of hydro heuristic policy.
        hydro_pricing_mode: Choice of hydro pricing mode.
        power_fluctuations: Choice of power fluctuation.
        shedding_policy: Choice of shedding policy.
        unit_commitment_mode: Choice of unit commitment mode.
        number_of_cores_mode: Choice of the number of cores mode.
        renewable_generation_modelling: Choice of the renewable generation modelling.
        accuracy_on_correlation: Choice of a set of elements in `OutputChoices`.
        initial_reservoir_levels: *Parameter removed since v9.2.*
    """
    hydro_heuristic_policy: HydroHeuristicPolicy = HydroHeuristicPolicy.ACCOMMODATE_RULES_CURVES
    hydro_pricing_mode: HydroPricingMode = HydroPricingMode.FAST
    power_fluctuations: PowerFluctuation = PowerFluctuation.FREE_MODULATIONS
    shedding_policy: SheddingPolicy = SheddingPolicy.SHAVE_PEAKS
    unit_commitment_mode: UnitCommitmentMode = UnitCommitmentMode.FAST
    number_of_cores_mode: SimulationCore = SimulationCore.MEDIUM
    renewable_generation_modelling: RenewableGenerationModeling = RenewableGenerationModeling.CLUSTERS
    accuracy_on_correlation: set[OutputChoices] = field(default_factory=set)
    # Parameter removed since v9.2
    initial_reservoir_levels: InitialReservoirLevel | None = None  # was InitialReservoirLevel.COLD_START in v8.8
    # Parameter introduced ince v9.3
    accurate_shave_peaks_include_short_term_storage: bool | None = None


@dataclass(frozen=True)
class SeedParameters:
    """Random seeds used for the random number generation by the simulator.

    TODO: Explain what is a seed and why it is important for reproducible simulations.
    TODO: Check number of seeds and coherence with UI.
    
    Attributes:
        seed_tsgen_thermal: Seed for the generation of thermal time-series.
        seed_tsnumbers: Seed for the generation of time-series (wind, load, hydro, solar, draws) (?)
        seed_unsupplied_energy_costs: Seed for the noise on unsupplied energy cost.
        seed_spilled_energy_costs: Seed for the noise on spilled energy costs.
        seed_thermal_costs: Seed for the noise on thermal plants costs.
        seed_hydro_costs: Seed for the noise on virtual hydro costs.
        seed_initial_reservoir_levels: Seed for initial reservoir levels.
    """
    seed_tsgen_thermal: int = 3005489
    seed_tsnumbers: int = 5005489
    seed_unsupplied_energy_costs: int = 6005489
    seed_spilled_energy_costs: int = 7005489
    seed_thermal_costs: int = 8005489
    seed_hydro_costs: int = 9005489
    seed_initial_reservoir_levels: int = 10005489


@dataclass
class AdvancedParametersUpdate:
    """Update advanced parameters.
    
    See the class [`AdvancedParameters`][antares.craft.model.settings.advanced_parameters.AdvancedParameters] for details of the fields.
    """
    initial_reservoir_levels: Optional[InitialReservoirLevel] = None
    hydro_heuristic_policy: Optional[HydroHeuristicPolicy] = None
    hydro_pricing_mode: Optional[HydroPricingMode] = None
    power_fluctuations: Optional[PowerFluctuation] = None
    shedding_policy: Optional[SheddingPolicy] = None
    unit_commitment_mode: Optional[UnitCommitmentMode] = None
    number_of_cores_mode: Optional[SimulationCore] = None
    renewable_generation_modelling: Optional[RenewableGenerationModeling] = None
    accuracy_on_correlation: Optional[set[OutputChoices]] = None
    accurate_shave_peaks_include_short_term_storage: Optional[bool] = None


@dataclass
class SeedParametersUpdate:
    """Update random seeds used for the random number generation by the simulator.
    
    See the class [`SeedParameters`][antares.craft.model.settings.advanced_parameters.SeedParameters] for details of the fields.
    """
    seed_tsgen_thermal: Optional[int] = None
    seed_tsnumbers: Optional[int] = None
    seed_unsupplied_energy_costs: Optional[int] = None
    seed_spilled_energy_costs: Optional[int] = None
    seed_thermal_costs: Optional[int] = None
    seed_hydro_costs: Optional[int] = None
    seed_initial_reservoir_levels: Optional[int] = None
