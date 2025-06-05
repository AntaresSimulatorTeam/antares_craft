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
    WARNING_DRY = "warning-dry"
    WARNING_VERBOSE = "warning-verbose"
    ERROR_DRY = "error-dry"
    ERROR_VERBOSE = "error-verbose"


class SimplexOptimizationRange(Enum):
    DAY = "day"
    WEEK = "week"


class ExportMPS(Enum):
    TRUE = True
    FALSE = False
    OPTIM1 = "optim1"
    OPTIM2 = "optim2"


@dataclass(frozen=True)
class OptimizationParameters:
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


@dataclass
class OptimizationParametersUpdate:
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
    include_exportstructure: Optional[bool] = None
    include_unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior] = None
