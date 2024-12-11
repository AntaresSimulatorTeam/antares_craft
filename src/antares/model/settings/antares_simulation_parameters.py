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

from typing import Optional

from antares.model.settings.solver import Solver


class AntaresSimulationParameters:
    def __init__(
        self,
        solver: Solver,
        nb_cpu: Optional[int] = None,
        unzip_output: bool = True,
        output_suffix: Optional[str] = None,
        presolve: bool = False,
    ):
        self.solver = solver
        self.nb_cpu = nb_cpu
        self.unzip_output = unzip_output
        self.output_suffix = output_suffix
        self.presolve = presolve
