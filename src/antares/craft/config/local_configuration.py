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

from antares.craft.config.base_configuration import BaseConfiguration


class LocalConfiguration(BaseConfiguration):
    """Configuration for accessing and modifying studies on your machine."""

    def __init__(self, local_path: Path, study_name: str):
        """Initialize your local configuration.

        Args:
            local_path: Path to the parent folder of your study.
            study_name: Name of your study.
        """
        self._study_path = local_path / study_name

    @property
    def study_path(self) -> Path:
        """Path to the study on your disc."""
        return self._study_path
