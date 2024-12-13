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

from typing import Optional, Union, Any, Dict

from pydantic import BaseModel, Field

from antares.model.settings.solver import Solver


class AntaresSimulationParameters(BaseModel):
    solver: Solver = Solver.SIRIUS
    nb_cpu: Optional[int] = None
    unzip_output: bool = Field(True, alias="auto_unzip")
    output_suffix: Optional[str] = None
    presolve: bool = False

    @property
    def other_options(self) -> str:
        options = []
        if self.presolve:
            options.append("presolve")
        if self.solver != Solver.SIRIUS:
            options.append(self.solver.name.lower())
        return " ".join(options)

    def model_dump(self, *args: Any, **kwargs: Any) -> Dict[str, Any]:
        data = super().model_dump(*args, **kwargs, by_alias=True)
        data["other_options"] = self.other_options
        data.pop("solver", None)
        data.pop("presolve", None)
        return data