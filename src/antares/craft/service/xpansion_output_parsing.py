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


from datetime import datetime

from antares.craft.model.output import (
    XpansionOutputAntares,
    XpansionOutputCandidate,
    XpansionOutputCandidateInvest,
    XpansionOutputCandidateSensitivity,
    XpansionOutputIteration,
    XpansionOutputOptions,
    XpansionOutputSensitivitySolution,
    XpansionOutputSolution,
    XpansionResult,
    XpansionSensitivityResult,
)
from antares.craft.tools.serde_local.json import from_json


def parse_xpansion_out_json(content: str) -> XpansionResult:
    json_content = from_json(content)

    antares = XpansionOutputAntares(version=json_content["antares"]["version"])
    antares_xpansion = XpansionOutputAntares(version=json_content["antares_xpansion"]["version"])

    options_json = json_content["options"]
    options = XpansionOutputOptions(
        log_level=options_json["LOG_LEVEL"],
        master_name=options_json["MASTER_NAME"],
        problem_format=options_json["PROBLEM_FORMAT"],
        solver_name=options_json["SOLVER_NAME"],
    )

    solution_json = json_content["solution"]
    solution = XpansionOutputSolution(
        investment_cost=solution_json["investment_cost"],
        iteration=solution_json["iteration"],
        operational_cost=solution_json["operational_cost"],
        optimality_gap=solution_json["optimality_gap"],
        overall_cost=solution_json["overall_cost"],
        problem_status=solution_json["problem_status"],
        relative_gap=solution_json["relative_gap"],
        stopping_criterion=solution_json["stopping_criterion"],
    )

    iterations_json = json_content["iterations"]
    iterations_cdt: dict[str, dict[int, XpansionOutputCandidateInvest]] = {}
    max_min = {}
    iterations = {}
    for key, value in iterations_json.items():
        json_candidates = value["candidates"]
        for json_cdt in json_candidates:
            iterations_cdt.setdefault(json_cdt["name"], {})[int(key)] = XpansionOutputCandidateInvest(
                invest=json_cdt["invest"]
            )
            max_min[json_cdt["name"]] = (json_cdt["max"], json_cdt["min"])

            iterations[int(key)] = XpansionOutputIteration(
                best_ub=value["best_ub"],
                cumulative_number_of_subproblem_resolutions=value["cumulative_number_of_subproblem_resolutions"],
                investment_cost=value["investment_cost"],
                lb=value["lb"],
                master_duration=value["master_duration"],
                operational_cost=value["operational_cost"],
                optimality_gap=value["optimality_gap"],
                overall_cost=value["overall_cost"],
                relative_gap=value["relative_gap"],
                subproblem_duration=value["subproblem_duration"],
                ub=value["ub"],
            )

    candidates = {}
    for key, value in solution_json["values"].items():
        iterations_not_sorted = iterations_cdt[key]
        iterations_sorted = dict(sorted(iterations_not_sorted.items()))
        candidates[key] = XpansionOutputCandidate(
            solution=value, max=max_min[key][0], min=max_min[key][1], iterations=list(iterations_sorted.values())
        )

    return XpansionResult(
        antares=antares,
        antares_xpansion=antares_xpansion,
        begin=datetime.strptime(json_content["begin"], "%d-%m-%Y %H:%M:%S"),
        end=datetime.strptime(json_content["end"], "%d-%m-%Y %H:%M:%S"),
        iterations=iterations,
        nb_weeks=json_content["nbWeeks"],
        options=options,
        run_duration=json_content["run_duration"],
        solution=solution,
        candidates=candidates,
    )


def parse_xpansion_sensitivity_out_json(content: str) -> XpansionSensitivityResult:
    json_content = from_json(content)

    antares = XpansionOutputAntares(version=json_content["antares"]["version"])
    antares_xpansion = XpansionOutputAntares(version=json_content["antares_xpansion"]["version"])

    candidates_minmax: dict[str, dict[str, XpansionOutputCandidateInvest]] = {}
    sensi_solutions = {}
    for json_solution in json_content["sensitivity solutions"]:
        direction = json_solution["optimization direction"]
        for cdt in json_solution["candidates"]:
            candidates_minmax.setdefault(cdt["name"], {})[direction] = XpansionOutputCandidateInvest(cdt["invest"])
        sensi_solutions[direction] = XpansionOutputSensitivitySolution(
            objective=json_solution["objective"],
            problem_type=json_solution["problem type"],
            status=json_solution["status"],
            system_cost=json_solution["system cost"],
        )

    candidates = {}
    for bounds_json in json_content["candidates bounds"]:
        cdt_name = bounds_json["name"]
        candidates[cdt_name] = XpansionOutputCandidateSensitivity(
            lb=bounds_json["lower bound"],
            ub=bounds_json["upper bound"],
            solution_max=candidates_minmax[cdt_name]["max"],
            solution_min=candidates_minmax[cdt_name]["min"],
        )

    return XpansionSensitivityResult(
        antares=antares,
        antares_xpansion=antares_xpansion,
        best_benders_cost=json_content["best benders cost"],
        epsilon=json_content["epsilon"],
        solution_max=sensi_solutions["max"],
        solution_min=sensi_solutions["min"],
        candidates=candidates,
    )
