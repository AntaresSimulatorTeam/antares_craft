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

from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


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
    model_config = ConfigDict(use_enum_values=True)

    simplex_optimization_range: SimplexOptimizationRange = Field(
        default=SimplexOptimizationRange.WEEK, validate_default=True
    )
    transmission_capacities: Union[bool, Union[LegacyTransmissionCapacities, OptimizationTransmissionCapacities]] = (
        Field(default=OptimizationTransmissionCapacities.LOCAL_VALUES, validate_default=True)
    )
    binding_constraints: bool = True
    hurdle_costs: bool = True
    thermal_clusters_min_stable_power: bool = True
    thermal_clusters_min_ud_time: bool = True
    day_ahead_reserve: bool = True
    strategic_reserve: bool = True
    spinning_reserve: bool = True
    primary_reserve: bool = True
    export_mps: ExportMPS = Field(default=ExportMPS.NONE, validate_default=True)
    include_exportstructure: bool = False
    unfeasible_problem_behavior: UnfeasibleProblemBehavior = Field(
        default=UnfeasibleProblemBehavior.ERROR_VERBOSE, validate_default=True
    )


@all_optional_model
class OptimizationParameters(DefaultOptimizationParameters):
    pass


class OptimizationParametersLocal(DefaultOptimizationParameters):
    @property
    def ini_fields(self) -> dict:
        return {
            "optimization": {
                "simplex-range": self.simplex_optimization_range,
                "transmission-capacities": self.transmission_capacities,
                "include-constraints": str(self.binding_constraints).lower(),
                "include-hurdlecosts": str(self.hurdle_costs).lower(),
                "include-tc-minstablepower": str(self.thermal_clusters_min_stable_power).lower(),
                "include-tc-min-ud-time": str(self.thermal_clusters_min_ud_time).lower(),
                "include-dayahead": str(self.day_ahead_reserve).lower(),
                "include-strategicreserve": str(self.primary_reserve).lower(),
                "include-spinningreserve": str(self.spinning_reserve).lower(),
                "include-primaryreserve": str(self.primary_reserve).lower(),
                "include-exportmps": self.export_mps,
                "include-exportstructure": str(self.include_exportstructure).lower(),
                "include-unfeasible-problem-behavior": self.unfeasible_problem_behavior,
            }
        }
