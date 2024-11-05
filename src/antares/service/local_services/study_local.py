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

from typing import Any, Optional

from antares.config.local_configuration import LocalConfiguration
from antares.model.binding_constraint import BindingConstraint
from antares.model.settings.study_settings import StudySettings
from antares.service.base_services import BaseStudyService


class StudyLocalService(BaseStudyService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._study_name = study_name

    @property
    def study_id(self) -> str:
        return self._study_name

    @property
    def config(self) -> LocalConfiguration:
        return self._config

    def update_study_settings(self, settings: StudySettings) -> Optional[StudySettings]:
        raise NotImplementedError

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        raise NotImplementedError

    def delete(self, children: bool) -> None:
        raise NotImplementedError
