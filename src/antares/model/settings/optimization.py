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
from typing import Optional, Union

from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class LegacyTransmissionCapacities(Enum):
    INFINITE = "infinite"


class TransmissionCapacities(Enum):
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


class OptimizationParameters(BaseModel, alias_generator=to_camel):
    binding_constraints: Optional[bool] = None
    hurdle_costs: Optional[bool] = None
    transmission_capacities: Union[bool, Union[LegacyTransmissionCapacities, TransmissionCapacities], None] = None
    thermal_clusters_min_stable_power: Optional[bool] = None
    thermal_clusters_min_ud_time: Optional[bool] = None
    day_ahead_reserve: Optional[bool] = None
    primary_reserve: Optional[bool] = None
    strategic_reserve: Optional[bool] = None
    spinning_reserve: Optional[bool] = None
    export_mps: Union[bool, str, None] = None
    unfeasible_problem_behavior: Optional[UnfeasibleProblemBehavior] = None
    simplex_optimization_range: Optional[SimplexOptimizationRange] = None
