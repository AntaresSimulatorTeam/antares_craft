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
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.binding_constraint import BindingConstraint
from antares.craft.model.output import Output
from antares.craft.service.base_services import BaseOutputService, BaseStudyService
from typing_extensions import override

if TYPE_CHECKING:
    from antares.craft.model.study import Study


class StudyLocalService(BaseStudyService):
    def __init__(self, config: LocalConfiguration, study_name: str, output_service: BaseOutputService) -> None:
        self._config = config
        self._study_name = study_name
        self._output_service: BaseOutputService = output_service

    @property
    @override
    def study_id(self) -> str:
        return self._study_name

    @property
    @override
    def config(self) -> LocalConfiguration:
        return self._config

    @property
    def output_service(self) -> BaseOutputService:
        return self._output_service

    @override
    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        raise NotImplementedError

    @override
    def delete(self, children: bool) -> None:
        raise NotImplementedError

    @override
    def create_variant(self, variant_name: str) -> "Study":
        raise NotImplementedError

    @override
    def read_outputs(self) -> list[Output]:
        raise NotImplementedError

    @override
    def delete_outputs(self) -> None:
        raise NotImplementedError

    @override
    def delete_output(self, output_name: str) -> None:
        raise NotImplementedError

    @override
    def move_study(self, new_parent_path: Path) -> PurePath:
        raise NotImplementedError

    @override
    def generate_thermal_timeseries(self, number_of_years: int) -> None:
        raise NotImplementedError
