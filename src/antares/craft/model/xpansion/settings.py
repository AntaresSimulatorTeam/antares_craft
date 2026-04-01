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
from dataclasses import asdict, dataclass
from typing import Optional

from antares.craft.tools.contents_tool import EnumIgnoreCase


class UcType(EnumIgnoreCase):
    """Unit-commitment type parameter.

    Specify the simulation mode used by Antares to evaluate the operating costs of the electrical system.
    
    Attributes:
        EXPANSION_FAST: Deactivate the flexibility constraints of the thermal units (Pmin constraints and minimum up and down times), 
            and do not take into account either the start-up costs or the impact of the day-ahead reserve.
        EXPANSION_ACCURATE: Unit-commitment variables are relaxed. The flexibility constraints
            of the thermal units as well as the start-up costs are taken into account.
    """
    EXPANSION_FAST = "expansion_fast"
    EXPANSION_ACCURATE = "expansion_accurate"


class Master(EnumIgnoreCase):
    """Master problem parameter.
    
    Specify how the integer variables are taken into account in Xpansion master problem.
    For problems with several investment candidates with large max-units, 
    using master = relaxed can accelerate the Antares-Xpansion algorithm very significantly.

    Attributes:
        INTEGER: The investment problem is solved by taking into account unit-size constraints of the candidates. 
            The master problem is a MILP (Mixed-Integer Linear Program).
        RELAXED: The integer variables are relaxed, and the level constraints of the investment candidates 
            (cf. `unit_size`) will not be necessarily respected. The master problem is linear.
    """
    INTEGER = "integer"
    RELAXED = "relaxed"


class XpansionSolver(EnumIgnoreCase):
    """Xpansion solver setting for the master problem.

    The settings `CBC` and `COIN` are identical: depending on whether the problem has integer variables, 
    Antares-Xpansion calls either the linear solver (Clp) or the MILP solver (Cbc) of the COIN-OR optimization suite.
    
    Attributes:
        CBC: [Cbc solver](https://github.com/coin-or/Cbc)
        COIN: [COIN-OR](https://github.com/coin-or/Clp)
        XPRESS: [Fico Xpress Optimization](https://www.fico.com/en/products/fico-xpress-optimization)
    """
    CBC = "Cbc"
    COIN = "Coin"
    XPRESS = "Xpress"


@dataclass(frozen=True)
class XpansionSettings:
    r"""Xpansion settings.
    
    Attributes:
        master: Master problem parameter for the treatment of integers (`INTEGER` or `RELAXED`)
        uc_type: Unit-commitment type (`EXPANSION_FAST` or `EXPANSION_ACCURATE`)
        optimality_gap: Optimality gap, tolerance on the absolute gap for the Antares-Xpansion algorithm in €.  
            At each iteration, the algorithm computes upper and lower bounds on the optimal cost.
            The algorithm stops as soon as the quantity `best_upper_bound - best_lower_bound` falls below `optimality_gap`.
            Note that if `optimality_gap = 0`, Antares-Xpansion will continue its search until the 
            optimal solution of the investment problem is found.
        relative_gap: At each iteration, the algorithm computes upper and lower bounds on the optimal cost. 
            The algorithm stops as soon as the quantity `(best_upper_bound - best_lower_bound) / max(|best_upper_bound|, |best_lower_bound|)`
            falls below relative_gap. For a relative gap $\alpha$, the cost of the solution returned by the algorithm satisfies:
            $$\frac{{\scriptstyle\texttt{xpansion solution cost}} - {\scriptstyle\texttt{optimal cost}}}{{\scriptstyle\texttt{optimal cost}}} < \alpha$$.
        relaxed_optimality_gap: The relaxed_optimality_gap parameter only has effect when master = integer. 
            In this case, the master problem is relaxed in the first iterations. 
            The relaxed_optimality_gap is the threshold from which to switch back from the relaxed to the integer master formulation.
        max_iteration: Maximum number of iterations for the Benders decomposition algorithm.
        solver: Solver used by the Bender decomposition (`CBC`, `COIN` or `XPRESS`).
        log_level: Solver's log severity. Possible values:
            - `log_level = 0` displays progress information for the investment on candidates and costs (see `reportbenders.txt`).
            - `log_level >= 1` displays information on the progress of the Benders algorithm (see `benders_solver.log`)
            - `log_level >= 1` display logs of the solver called for the resolution of each master or subproblem (see `solver_log_proc_<proc_num>.txt`). 
        separation_parameter: Define the step size for the in-out separation.
        batch_size: Number of subproblems per batch. If set to `0`, then all subproblems are in the same batch, 
            hence a classical Benders problem.
        yearly_weights: Filename of the array of weights. 
            It allows to assume that the Monte Carlo years simulated in the Antares study are not equally probable
        additional_constraints: Filename located in the `user/expansion/constraints` folder of the Antares study.
            TODO: link to model of the file
        timelimit: Maximum allowed time in seconds for the execution of a Benders step of Antares-Xpansion.
        master_solution_tolerance: Control the tolerance used when rounding the solution variables of the master problem.
        cut_coefficient_tolerance: Define the tolerance under which cuts coefficients and right-hand sides are considered to be zero.
    """
    master: Master = Master.INTEGER
    uc_type: UcType = UcType.EXPANSION_FAST
    optimality_gap: float = 1
    relative_gap: float = 1e-6
    relaxed_optimality_gap: float = 1e-5
    max_iteration: int = 1000
    solver: XpansionSolver = XpansionSolver.XPRESS
    log_level: int = 0
    separation_parameter: float = 0.5
    batch_size: int = 96
    yearly_weights: Optional[str] = None
    additional_constraints: Optional[str] = None
    timelimit: int = int(1e12)
    master_solution_tolerance: float = 1e-4
    cut_coefficient_tolerance: float = 5e-3


@dataclass
class XpansionSettingsUpdate:
    r"""Xpansion settings update.
    
    Attributes:
        master: Master problem parameter for the treatment of integers (`INTEGER` or `RELAXED`)
        uc_type: Unit-commitment type (`EXPANSION_FAST` or `EXPANSION_ACCURATE`)
        optimality_gap: Optimality gap, tolerance on the absolute gap for the Antares-Xpansion algorithm in €.  
            At each iteration, the algorithm computes upper and lower bounds on the optimal cost.
            The algorithm stops as soon as the quantity `best_upper_bound - best_lower_bound` falls below `optimality_gap`.
            Note that if `optimality_gap = 0`, Antares-Xpansion will continue its search until the 
            optimal solution of the investment problem is found.
        relative_gap: At each iteration, the algorithm computes upper and lower bounds on the optimal cost. 
            The algorithm stops as soon as the quantity `(best_upper_bound - best_lower_bound) / max(|best_upper_bound|, |best_lower_bound|)`
            falls below relative_gap. For a relative gap $\alpha$, the cost of the solution returned by the algorithm satisfies:
            $$\frac{{\scriptstyle\texttt{xpansion solution cost}} - {\scriptstyle\texttt{optimal cost}}}{{\scriptstyle\texttt{optimal cost}}} < \alpha$$.
        relaxed_optimality_gap: The relaxed_optimality_gap parameter only has effect when master = integer. 
            In this case, the master problem is relaxed in the first iterations. 
            The relaxed_optimality_gap is the threshold from which to switch back from the relaxed to the integer master formulation.
        max_iteration: Maximum number of iterations for the Benders decomposition algorithm.
        solver: Solver used by the Bender decomposition (`CBC`, `COIN` or `XPRESS`).
        log_level: Solver's log severity. Possible values:
            - `log_level = 0` displays progress information for the investment on candidates and costs (see `reportbenders.txt`).
            - `log_level >= 1` displays information on the progress of the Benders algorithm (see `benders_solver.log`)
            - `log_level >= 1` display logs of the solver called for the resolution of each master or subproblem (see `solver_log_proc_<proc_num>.txt`). 
        separation_parameter: Define the step size for the in-out separation.
        batch_size: Number of subproblems per batch. If set to `0`, then all subproblems are in the same batch, 
            hence a classical Benders problem.
        yearly_weights: Filename of the array of weights. 
            It allows to assume that the Monte Carlo years simulated in the Antares study are not equally probable
        additional_constraints: Filename located in the `user/expansion/constraints` folder of the Antares study.
            TODO: link to model of the file
        timelimit: Maximum allowed time in seconds for the execution of a Benders step of Antares-Xpansion.
        master_solution_tolerance: Control the tolerance used when rounding the solution variables of the master problem.
        cut_coefficient_tolerance: Define the tolerance under which cuts coefficients and right-hand sides are considered to be zero.
    """
    master: Optional[Master] = None
    uc_type: Optional[UcType] = None
    optimality_gap: Optional[float] = None
    relative_gap: Optional[float] = None
    relaxed_optimality_gap: Optional[float] = None
    max_iteration: Optional[int] = None
    solver: Optional[XpansionSolver] = None
    log_level: Optional[int] = None
    separation_parameter: Optional[float] = None
    batch_size: Optional[int] = None
    yearly_weights: Optional[str] = None
    additional_constraints: Optional[str] = None
    timelimit: Optional[int] = None
    master_solution_tolerance: Optional[float] = None
    cut_coefficient_tolerance: Optional[float] = None


def update_xpansion_settings(settings: XpansionSettings, settings_update: XpansionSettingsUpdate) -> XpansionSettings:
    """Update Xpansion settings.
    
    Args:
        settings: The original settings.
        settings_update: The new settings to update.

    Returns:
        The updated settings.
    """
    settings_dict = asdict(settings)
    update_dict = {k: v for k, v in asdict(settings_update).items() if v is not None}
    settings_dict.update(update_dict)

    return XpansionSettings(**settings_dict)
