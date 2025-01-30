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

from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel
from pydantic.alias_generators import to_camel


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


@all_optional_model
class OptimizationParametersAPI(BaseModel, alias_generator=to_camel):
    simplex_optimization_range: SimplexOptimizationRange
    transmission_capacities: OptimizationTransmissionCapacities
    binding_constraints: bool
    hurdle_costs: bool
    thermal_clusters_min_stable_power: bool
    thermal_clusters_min_ud_time: bool
    day_ahead_reserve: bool
    strategic_reserve: bool
    spinning_reserve: bool
    primary_reserve: bool
    export_mps: ExportMPS
    include_exportstructure: bool
    unfeasible_problem_behavior: UnfeasibleProblemBehavior


class OptimizationParametersLocalCreation(BaseModel, alias_generator=to_kebab):
    simplex_range: SimplexOptimizationRange = SimplexOptimizationRange.WEEK
    transmission_capacities: OptimizationTransmissionCapacities = OptimizationTransmissionCapacities.LOCAL_VALUES
    include_constraints: bool = True
    include_hurdle_costs: bool = True
    include_tc_min_stable_power: bool = True
    include_tc_min_ud_time: bool = True
    include_dayahead: bool = True
    include_strategicreserve: bool = True
    include_spinningreserve: bool = True
    include_primaryreserve: bool = True
    include_exportmps: bool = False
    include_exportstructure: bool = False
    include_unfeasible_problem_behavior: UnfeasibleProblemBehavior = UnfeasibleProblemBehavior.ERROR_VERBOSE


@all_optional_model
class OptimizationSettingsLocalEdition(OptimizationParametersLocalCreation):
    pass
