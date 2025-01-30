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


class OptimizationTransmissionCapacities(Enum):
    LOCAL_VALUES = "local-values"
    NULL_FOR_ALL_LINKS = "null-for-all-links"
    INFINITE_FOR_ALL_LINKS = "infinite-for-all-links"
    NULL_FOR_PHYSICAL_LINKS = "null-for-physical-links"
    INFINITE_FOR_PHYSICAL_LINKS = "infinite-for-physical-links"


class UnfeasibleProblemBehavior(Enum):
    WARNING_DRY = "warning-dry"
    WARNING_VERBOSE = "warning-verbose"
    ERROR_DRY = "error-dry"
    ERROR_VERBOSE = "error-verbose"


class SimplexOptimizationRange(Enum):
    DAY = "day"
    WEEK = "week"


class ExportMPS(Enum):
    NONE = "none"
    OPTIM1 = "optim1"
    OPTIM2 = "optim2"
    BOTH_OPTIMS = "both-optims"


@dataclass
class OptimizationParameters:
    simplex_range: Optional[SimplexOptimizationRange] = None
    transmission_capacities: Optional[OptimizationTransmissionCapacities] = None
    include_constraints: Optional[bool] = None
    include_hurdle_costs: Optional[bool] = None
    include_thermal_cluster_min_stable_power: Optional[bool] = None
    include_thermal_cluster_min_ud_time: Optional[bool] = None
    include_day_ahead: Optional[bool] = None
    include_strategic_reserve: Optional[bool] = None
    include_spinning_reserve: Optional[bool] = None
    include_primary_reserve: Optional[bool] = None
    include_export_mps: Optional[ExportMPS] = None
    include_export_structure: Optional[bool] = None
    include_unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior] = None
