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
from datetime import datetime
from enum import Enum
from typing import Optional

import pandas as pd

from antares.craft.exceptions.exceptions import OutputDataRetrievalError
from antares.craft.service.base_services import BaseOutputService


class MCIndAreasDataType(Enum):
    """TODO
    """
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasDataType(Enum):
    """TODO
    """
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksDataType(Enum):
    """TODO
    """
    VALUES = "values"


class MCAllLinksDataType(Enum):
    VALUES = "values"
    ID = "id"


class Frequency(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass(frozen=True)
class XpansionOutputAntares:
    """Output of Xpansion investment module.
    
    Attributes:
        version: The version of the module used in the simulation.
    """
    version: str


@dataclass(frozen=True)
class XpansionOutputOptions:
    """Options of Xpansion output.

    Attributes:
        log_level: Solver's log severity in {0, 1, 2}. TODO: put link to details
        master_name: TODO: is it a user defined name of the master problem ? 
        problem_format: TODO: ?
        solver_name: Solver used for the resolution of the optimization problem.
    """
    log_level: int
    master_name: str
    problem_format: str
    solver_name: str


@dataclass(frozen=True)
class XpansionOutputIteration:
    """Xpansion output for a given iteration.
    
    Attributes:
        best_ub: Best upper bound on the optimal cost. 
        cumulative_number_of_subproblem_resolutions: TODO:
        investment_cost: Investment cost chosen by the algorithm for this iteration.
        lb: The lower bound of the optimal cost which is the solution of the master problem as it is a relaxation of the investment problem.
        master_duration: Duration of the master problem resolution.
        operational_cost: TODO: is it ? The yearly output cost of an Antares Simulation for the system with a given investment level. 
        optimality_gap: Absolute gap between the underestimator and the Antares simulation (`(up - lb) / lb`).
        overall_cost: TODO: is it ? The yearly overall cost corresponds to the sum of the operational cost.
            and the product of the annualized cost per MW and the investment in MW.
        relative_gap: At each iteration, the algorithm computes upper and lower bounds on the optimal cost. 
            The algorithm stops as soon as the quantity `(best_upper_bound - best_lower_bound) / max(|best_upper_bound|, |best_lower_bound|)`
            falls below relative_gap. For a relative gap $\alpha$, the cost of the solution returned by the algorithm satisfies:
            $$\frac{{\scriptstyle\texttt{xpansion solution cost}} - {\scriptstyle\texttt{optimal cost}}}{{\scriptstyle\texttt{optimal cost}}} < \alpha$$.
        subproblem_duration: TODO: is it ? Subproblem duration corresponding to the weekly Antares problem.
        ub: TODO: difference with best upper bound ?
    """
    best_ub: float
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


@dataclass(frozen=True)
class XpansionOutputSolution:
    """Xpansion output solution.
    
    Attributes:
        investment_cost: optimal investment cost found by the algorithm.
        iteration: Corresponding iteration for the best solution
        operational_cost: Operational cost TODO: what's inside ?
        optimality_gap: Absolute gap between the underestimator and the Antares simulation (`(up - lb) / lb`).
        overall_cost: TODO: is it ? The yearly overall cost corresponds to the sum of the operational cost.
        problem_status: Problem status.
        relative_gap: At each iteration, the algorithm computes upper and lower bounds on the optimal cost. 
            The algorithm stops as soon as the quantity `(best_upper_bound - best_lower_bound) / max(|best_upper_bound|, |best_lower_bound|)`
            falls below relative_gap. For a relative gap $\alpha$, the cost of the solution returned by the algorithm satisfies:
            $$\frac{{\scriptstyle\texttt{xpansion solution cost}} - {\scriptstyle\texttt{optimal cost}}}{{\scriptstyle\texttt{optimal cost}}} < \alpha$$.
        stopping_criterion: Stopping criterion for the optimization problem.
    """
    investment_cost: float
    iteration: int
    operational_cost: float
    optimality_gap: float
    overall_cost: float
    problem_status: str
    relative_gap: float
    stopping_criterion: str


@dataclass(frozen=True)
class XpansionOutputCandidateInvest:
    """Xpansion output candidate investment.
    
    Attributes:
        invest: Amount of investment for a given candidate.
    """
    invest: float


@dataclass(frozen=True)
class XpansionOutputCandidate:
    """Xpansion output candidate.
    
    Attributes:
        solution: TODO:
        max: TODO:
        min: TODO:
        iterations: List of the output candidate investment for each iteration.
    """
    solution: float
    max: float
    min: float
    iterations: list[XpansionOutputCandidateInvest]


@dataclass(frozen=True)
class XpansionResult:
    """Xpansion results.
    
    Attributes:
        antares: XpansionOutputAntares
        antares_xpansion: XpansionOutputAntares
        begin: Timestamp of the start of the problem resolution.
        end: Timestamp of the end of the problem resolution.
        iterations: Dictionnary of all the iterations of the problem and the corresponding pieces of information.
        nb_weeks: TODO:
        options: Options for Xpansion module.
        run_duration: Duration of the problem resolution.
        solution: Final optimal solution.
        candidates: Dictionnary of all candidates.
    """
    antares: XpansionOutputAntares # strange that it is the same version ?
    antares_xpansion: XpansionOutputAntares
    begin: datetime
    end: datetime
    iterations: dict[int, XpansionOutputIteration]
    nb_weeks: int
    options: XpansionOutputOptions
    run_duration: float
    solution: XpansionOutputSolution
    candidates: dict[str, XpansionOutputCandidate]


@dataclass(frozen=True)
class XpansionOutputCandidateSensitivity:
    """Xpansion output candidate sensitivity study.
    
    Attributes:
        lb: TODO:
        ub: TODO:
        solution_max: TODO:
        solution_min: TODO:
    """
    lb: float
    ub: float
    solution_max: XpansionOutputCandidateInvest
    solution_min: XpansionOutputCandidateInvest


@dataclass(frozen=True)
class XpansionOutputSensitivitySolution:
    """Xpansion output sensibility solution.
    
    Attributes:
        objective: TODO:
        problem_type: TODO:
        status: TODO:
        system_cost: TODO:
    """
    objective: float
    problem_type: str
    status: int
    system_cost: float


@dataclass(frozen=True)
class XpansionSensitivityResult:
    """Xpansion sensitivity results.
    
    Attributes:
        antares:TODO:
        antares_xpansion:TODO:
        best_benders_cost:TODO:
        epsilon:TODO:
        candidates:TODO:
        solution_max:TODO:
        solution_min:TODO:
    """
    antares: XpansionOutputAntares
    antares_xpansion: XpansionOutputAntares
    best_benders_cost: float
    epsilon: float
    candidates: dict[str, XpansionOutputCandidateSensitivity]
    solution_max: XpansionOutputSensitivitySolution
    solution_min: XpansionOutputSensitivitySolution


@dataclass
class AggregationEntry:
    """Represent an entry for aggregation queries

    Attributes:
        data_type: TODO:
        frequency: "hourly", "daily", "weekly", "monthly", "annual".
        mc_years: Monte Carlo years to include in the query. If left empty, all years are included.
        type_ids: which links/areas to be selected (ex: "be - fr"). If empty, all are selected.
        columns_names: names or regexes (if data_type is of type details) to select columns.
    """

    data_type: MCAllAreasDataType | MCIndAreasDataType | MCAllLinksDataType | MCIndLinksDataType
    frequency: Frequency
    mc_years: Optional[list[int]] = None
    type_ids: Optional[list[str]] = None
    columns_names: Optional[list[str]] = None


class Output:
    """Output of an Antares simulation with/without Xpansion."""

    def __init__(self, name: str, archived: bool, output_service: BaseOutputService):
        self._name = name
        self._archived = archived
        self._output_service: BaseOutputService = output_service

    @property
    def name(self) -> str:
        """Name of the output."""
        return self._name

    @property
    def archived(self) -> bool:
        """Whether the output is archived or not."""
        return self._archived

    def get_mc_all_area(self, frequency: Frequency, data_type: MCAllAreasDataType, area: str) -> pd.DataFrame:
        """

        Args:
            frequency: "hourly", "daily", "weekly", "monthly", "annual".
            data_type: the data-type of mc-all areas.
            area: the area name.

        Returns:

        """
        file_path = f"mc-all/areas/{area}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_all_link(
        self, frequency: Frequency, data_type: MCAllLinksDataType, area_from: str, area_to: str
    ) -> pd.DataFrame:
        """

        Args:
            frequency: "hourly", "daily", "weekly", "monthly", "annual".
            data_type: the data-type of mc-all links.
            area_from: area_from id.
            area_to: area_to id.

        Returns:

        """
        if [area_from, area_to] != sorted([area_from, area_to]):
            raise OutputDataRetrievalError(self.name, "Areas should be sorted alphabetically")
        file_path = f"mc-all/links/{area_from} - {area_to}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_ind_area(
        self, mc_year: int, frequency: Frequency, data_type: MCIndAreasDataType, area: str
    ) -> pd.DataFrame:
        """

        Args:
            mc_year:
            frequency: "hourly", "daily", "weekly", "monthly", "annual".
            data_type: the data-type of mc-ind areas.
            area: the area name.

        Returns:

        """
        file_path = f"mc-ind/{mc_year:05}/areas/{area}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_ind_link(
        self, mc_year: int, frequency: Frequency, data_type: MCIndLinksDataType, area_from: str, area_to: str
    ) -> pd.DataFrame:
        """

        Args:
            mc_year:
            frequency: "hourly", "daily", "weekly", "monthly", "annual".
            data_type: the data-type of mc-ind links.
            area_from: area_from id.
            area_to: area_to id.

        Returns:

        """
        if [area_from, area_to] != sorted([area_from, area_to]):
            raise OutputDataRetrievalError(self.name, "Areas should be sorted alphabetically")
        file_path = f"mc-ind/{mc_year:05}/links/{area_from} - {area_to}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def aggregate_mc_ind_areas(
        self,
        data_type: MCIndAreasDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Creates a matrix of aggregated raw data for areas with mc-ind

        Args:
            data_type: values from McIndAreasDataType.
            frequency: values from Frequency.

        Returns: 
            Aggregated raw data.
        """
        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "ind")

    def aggregate_mc_ind_links(
        self,
        data_type: MCIndLinksDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        links_ids: Optional[list[tuple[str, str]]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Creates a matrix of aggregated raw data for links with mc-ind

        Args:
            data_type: values from McIndLinks
            frequency: values from Frequency

        Returns:
            Aggregated raw data
        """
        type_ids = (
            [f"{area_from} - {area_to}" for link_id in links_ids for area_from, area_to in [sorted(link_id)]]
            if links_ids
            else None
        )

        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=type_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "ind")

    def aggregate_mc_all_areas(
        self,
        data_type: MCAllAreasDataType,
        frequency: Frequency,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Creates a matrix of aggregated raw data for areas with mc-all

        Args:
            data_type: values from McAllAreas
            frequency: values from Frequency

        Returns:
            Aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "all")

    def aggregate_mc_all_links(
        self,
        data_type: MCAllLinksDataType,
        frequency: Frequency,
        links_ids: Optional[list[tuple[str, str]]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """Creates a matrix of aggregated raw data for links with mc-all

        Args:
            data_type: values from McAllLinks
            frequency: values from Frequency

        Returns: 
            Aggregated raw data.
        """
        type_ids = (
            [f"{area_from} - {area_to}" for link_id in links_ids for area_from, area_to in [sorted(link_id)]]
            if links_ids
            else None
        )

        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            type_ids=type_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "all")

    def get_xpansion_result(self) -> XpansionResult:
        """

        Returns:

        """
        return self._output_service.get_xpansion_result(self.name)

    def get_xpansion_sensitivity_result(self) -> XpansionSensitivityResult:
        """
        
        Returns:

        """
        return self._output_service.get_xpansion_sensitivity_result(self.name)
