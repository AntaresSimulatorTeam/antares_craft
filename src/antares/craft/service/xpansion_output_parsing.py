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


from antares.craft.model.output import XpansionResult, XpansionSensitivityResult
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.serde_local.json import from_json


def to_upper(x: str) -> str:
    return x.upper()

class XpansionOutputAntares(APIBaseModel):
    version: str

class XpansionOutputOptions(APIBaseModel, alias_generator=to_upper):
    log_level: int
    master_name: str
    problem_format: str
    solver_name: str

class XpansionOutputSolutionValues(APIBaseModel):
    pass

class XpansionOutputIterationCandidate(APIBaseModel):
    invest: float
    max: float
    min: float
    name: str

class XpansionOutputIteration(APIBaseModel):
    best_ub: float
    candidates: list[XpansionOutputIterationCandidate]
    cumulative_number_of_subproblem_resolutions: int
    investment_cost: float
    lb: float
    master_duration: float
    operational_cost: float
    optimality_gap: float
    overall_cost: float
    relative_gap: float
    subproblem_duration: float
    ub: float


class XpansionOutputSolution(APIBaseModel):
    investment_cost: float
    iteration: int
    operational_cost: float
    optimality_gap: float
    overall_cost: float
    problem_status: str
    relative_gap: float
    stopping_criterion: str
    values: XpansionOutputSolutionValues

class XpansionOutput(APIBaseModel):
    antares: XpansionOutputAntares
    antares_xpansion: XpansionOutputAntares
    begin: str
    end: str
    iterations: dict[str, XpansionOutputIteration]
    nb_weeks: int
    options: XpansionOutputOptions
    run_duration: float
    solution: XpansionOutputSolution


def parse_xpansion_out_json(content: str) -> XpansionResult:
    json_content = from_json(content)
    internal_model = XpansionOutput.model_validate(json_content)



def parse_xpansion_sensitivity_out_json(content: str) -> XpansionSensitivityResult:
    json_content = from_json(content)
