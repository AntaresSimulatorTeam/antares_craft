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
from pathlib import Path
from typing import Any, Optional

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import AntaresSimulationRunningError
from antares.craft.model.simulation import AntaresSimulationParameters, Job
from antares.craft.service.base_services import BaseRunService
from typing_extensions import override


class RunLocalService(BaseRunService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def run_antares_simulation(
        self, parameters: Optional[AntaresSimulationParameters] = None, solver_path: Optional[Path] = None
    ) -> Job:
        if not solver_path:
            raise AntaresSimulationRunningError(self.study_name, "No solver path was provided")
        raise NotImplementedError

    @override
    def wait_job_completion(self, job: Job, time_out: int) -> None:
        raise NotImplementedError
