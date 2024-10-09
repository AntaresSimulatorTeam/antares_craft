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
from typing import Union

from pydantic import BaseModel
from pydantic.alias_generators import to_camel

from antares.tools.all_optional_meta import all_optional_model


class LegacyTransmissionCapacities(Enum):
    INFINITE = "infinite"


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
    FALSE = False
    NONE = "none"
    OPTIM1 = "optim1"
    OPTIM2 = "optim2"
    BOTH_OPTIMS = "both-optims"
    TRUE = True


class DefaultOptimizationParameters(BaseModel, alias_generator=to_camel):
    simplex_optimization_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK
    transmission_capacities: Union[bool, Union[LegacyTransmissionCapacities, OptimizationTransmissionCapacities]] = (
        OptimizationTransmissionCapacities.LOCAL_VALUES
    )
    binding_constraints: bool = True
    hurdle_costs: bool = True
    thermal_clusters_min_stable_power: bool = True
    thermal_clusters_min_ud_time: bool = True
    day_ahead_reserve: bool = True
    strategic_reserve: bool = True
    spinning_reserve: bool = True
    primary_reserve: bool = True
    export_mps: ExportMPS = ExportMPS.NONE
    include_exportstructure: bool = False
    unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE


@all_optional_model
class OptimizationParameters(DefaultOptimizationParameters):
    pass


class OptimizationParametersLocal(DefaultOptimizationParameters):
    pass
