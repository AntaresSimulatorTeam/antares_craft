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

from antares.config.base_configuration import BaseConfiguration


class LocalConfiguration(BaseConfiguration):
    def __init__(self, local_path: Path, study_name: str):
        self._local_path = local_path
        self._study_name = study_name

    @property
    def local_path(self) -> Path:
        return self._local_path

    @property
    def study_path(self) -> Path:
        return self._local_path / self._study_name
