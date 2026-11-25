# Copyright (c) 2024-2026, RTE (https://www.rte-france.com)
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
from dataclasses import asdict
from typing import Any

from antares.craft.model.commons import STUDY_VERSION_10_2
from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationParameters,
    OptimizationParametersUpdate,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModelAllowExtraValues
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.alias_generators import to_kebab
from antares.study.version import StudyVersion

OptimizationParametersType = OptimizationParameters | OptimizationParametersUpdate


class OptimizationParametersLocal(LocalBaseModelAllowExtraValues, alias_generator=to_kebab):
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
    # Since v10.2
    include_reserves: bool | None = None

    @staticmethod
    def from_user_model(user_class: OptimizationParametersType) -> "OptimizationParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return OptimizationParametersLocal.model_validate(user_dict)

    def to_user_model(self) -> OptimizationParameters:
        return OptimizationParameters(
            simplex_range=self.simplex_range,
            transmission_capacities=self.transmission_capacities,
            include_constraints=self.include_constraints,
            include_hurdlecosts=self.include_hurdlecosts,
            include_tc_minstablepower=self.include_tc_minstablepower,
            include_tc_min_ud_time=self.include_tc_min_ud_time,
            include_dayahead=self.include_dayahead,
            include_strategicreserve=self.include_strategicreserve,
            include_spinningreserve=self.include_spinningreserve,
            include_primaryreserve=self.include_primaryreserve,
            include_exportmps=self.include_exportmps,
            include_unfeasible_problem_behavior=self.include_unfeasible_problem_behavior,
            include_reserves=self.include_reserves,
        )


def validate_against_version(parameters: OptimizationParametersLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_10_2:
        check_min_version(parameters, "include_reserves", version)


def initialize_with_version(
    parameters: OptimizationParametersLocal, version: StudyVersion
) -> OptimizationParametersLocal:
    if version >= STUDY_VERSION_10_2:
        initialize_field_default(parameters, "include_reserves", False)
    return parameters


def parse_optimization_parameters_local(study_version: StudyVersion, data: Any) -> OptimizationParameters:
    local_parameters = OptimizationParametersLocal.model_validate(data.get("optimization", {}))
    validate_against_version(local_parameters, study_version)
    initialize_with_version(local_parameters, study_version)
    return local_parameters.to_user_model()


def serialize_optimization_parameters_local(
    parameters: OptimizationParametersType, study_version: StudyVersion, update: bool
) -> dict[str, Any]:
    local_parameters = OptimizationParametersLocal.from_user_model(parameters)
    validate_against_version(local_parameters, study_version)
    return local_parameters.model_dump(mode="json", by_alias=True, exclude_unset=update, exclude_none=True)
