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

from typing_extensions import override


class OptimizationTransmissionCapacities(Enum):
    """Optimization of transmission capacities.

    Allow the user to override the transmission capacities on links.

    Attributes:
        LOCAL_VALUES: Use the local property for all links, including physical links (no override).
        NULL_FOR_ALL_LINKS: Override all transmission capacities with 0.
        INFINITE_FOR_ALL_LINKS: Override all transmission capacities with inf.
        NULL_FOR_PHYSICAL_LINKS: Override transmission capacities with 0 **on physical links only**.
        INFINITE_FOR_PHYSICAL_LINKS: Override transmission capacities with inf **on physical links only**.
    """

    LOCAL_VALUES = "local-values"
    NULL_FOR_ALL_LINKS = "null-for-all-links"
    INFINITE_FOR_ALL_LINKS = "infinite-for-all-links"
    NULL_FOR_PHYSICAL_LINKS = "null-for-physical-links"
    INFINITE_FOR_PHYSICAL_LINKS = "infinite-for-physical-links"

    @classmethod
    @override
    def _missing_(cls, value: object) -> Optional["OptimizationTransmissionCapacities"]:
        """Handle legacy transmission capacities"""
        if isinstance(value, bool):
            if value:
                return OptimizationTransmissionCapacities.LOCAL_VALUES
            else:
                return OptimizationTransmissionCapacities.NULL_FOR_ALL_LINKS
        elif value == "infinite":
            return OptimizationTransmissionCapacities.INFINITE_FOR_ALL_LINKS
        return None


class UnfeasibleProblemBehavior(Enum):
    """Define the behaviour of the simulator in case of an unfeasible problem.

    Attributes:
        WARNING_DRY: Continue simulation.
        WARNING_VERBOSE: Continue simulation, but export the MPS file of the unfeasible problem.
        ERROR_DRY: Stop simulation.
        ERROR_MPS: Stop simulation, and export the MPS file of the unfeasible problem.
    """

    WARNING_DRY = "warning-dry"
    WARNING_VERBOSE = "warning-verbose"
    ERROR_DRY = "error-dry"
    ERROR_VERBOSE = "error-verbose"


class SimplexOptimizationRange(Enum):
    r"""Simplex optimization range.

    In the formulation of the optimal hydro-thermal unit-commitment and dispatch problem,
    the reference hydro energy $HIT$ used to set the right hand sides of hydro constraints depends
    on the value chosen for this parameter, and is defined as follows:
    - `day`: for each day d of week $\omega$ : $HIT = W_d^2$
    - `week`: for week $\omega$: $HIT = \sum_{d\in \omega}{W_d^2}$

    Weekly optimization performs a more refined unit-commitment, especially when `unit_commitment_mode` is set to `accurate`.

    Attributes:
        DAY:
        WEEK:
    """

    DAY = "day"
    WEEK = "week"


class ExportMPS(Enum):
    """Allow to export the optimization problem in MPS format.

    Attributes:
        TRUE: Export MPS for both steps of the optimization.
        FALSE: Do not export any MPS.
        OPTIM1: Export MPS only for the first step of the optimization.
        OPTIM2: Export MPS only for the second step of the optimization.
        BOTH_OPTIMS: Export MPS for both steps of the optimization.
    """

    TRUE = True
    FALSE = False
    OPTIM1 = "optim1"
    OPTIM2 = "optim2"
    BOTH_OPTIMS = "both-optims"


@dataclass(frozen=True)
class OptimizationParameters:
    """Optimization parameters.

    Attributes:
        simplex_range: Simplex optimization range (`WEEK` in general or `DAY`).
        transmission_capacities: Override transmission capacities (`LOCAL_VALUES`, `NULL_FOR_ALL_LINKS`,
            `INFINITE_FOR_ALL_LINKS`, `NULL_FOR_PHYSICAL_LINKS`, `INFINITE_FOR_PHYSICAL_LINKS`).
        include_constraints: Whether to include binding constraints.
        include_hurdlecosts: Whether to include hurdle costs.
        include_tc_minstablepower: Whether to activate the constraint of minimum stable power for thermal units.
        include_tc_min_ud_time: Whether to activate the constraint of minimum start-up time for thermal units.
        include_dayahead: Whether to activate day-ahead reserve constraints.
        include_strategicreserve: Whether to activate
        include_spinningreserve: Whether to activate
        include_primaryreserve: Whether to activate
        include_exportmps: Choices to export MPS files (`TRUE`, `FALSE`, `OPTIM1`, `OPTIM2`, or `BOTH_OPTIMS`).
        include_unfeasible_problem_behavior: Choices to export MPS files in case of an unfeasible problem
            (`WARNING_DRY`, `WARNING_VERBOSE`, `ERROR_DRY`, `ERROR_VERBOSE`).
    """

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
    include_unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE


@dataclass
class OptimizationParametersUpdate:
    """Update optimization parameters.

    See the class [`OptimizationParameters`][antares.craft.model.settings.optimization.OptimizationParameters] for details of the parameters.
    """

    simplex_range: Optional[SimplexOptimizationRange] = None
    transmission_capacities: Optional[OptimizationTransmissionCapacities] = None
    include_constraints: Optional[bool] = None
    include_hurdlecosts: Optional[bool] = None
    include_tc_minstablepower: Optional[bool] = None
    include_tc_min_ud_time: Optional[bool] = None
    include_dayahead: Optional[bool] = None
    include_strategicreserve: Optional[bool] = None
    include_spinningreserve: Optional[bool] = None
    include_primaryreserve: Optional[bool] = None
    include_exportmps: Optional[ExportMPS] = None
    include_unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior] = None
