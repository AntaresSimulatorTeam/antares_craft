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
from dataclasses import asdict
from typing import Any

from pydantic import field_validator

from antares.craft.model.settings.optimization import (
    ExportMPS,
    OptimizationParameters,
    OptimizationParametersUpdate,
    OptimizationTransmissionCapacities,
    SimplexOptimizationRange,
    UnfeasibleProblemBehavior,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab

OptimizationParametersType = OptimizationParameters | OptimizationParametersUpdate


class OptimizationParametersLocal(LocalBaseModel, alias_generator=to_kebab):
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

    @field_validator("include_exportmps", mode="before")
    def validate_export_mps(cls, v: Any) -> Any:
        # `False` and `None` are the same for the simulator
        if isinstance(v, str) and v.lower() == "none":
            v = False
        return v

    @staticmethod
    def from_user_model(user_class: OptimizationParametersType) -> "OptimizationParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return OptimizationParametersLocal.model_validate(user_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update)
        current_content.setdefault("optimization", {}).update(content)
        return current_content

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
            include_exportstructure=self.include_exportstructure,
            include_unfeasible_problem_behavior=self.include_unfeasible_problem_behavior,
        )
