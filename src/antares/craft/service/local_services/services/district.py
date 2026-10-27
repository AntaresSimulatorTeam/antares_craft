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

from typing import Any

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.tools.serde_local.ini_common import any_section_option_matcher
from antares.craft.tools.serde_local.ini_reader import IniReader


class DistrictLocalService:
    def __init__(self, config: LocalConfiguration, study_name: str) -> None:
        self.config = config
        self.study_name = study_name

    def read_ini(self) -> dict[str, Any]:
        """Read the raw district definitions from sets.ini."""
        reader = IniReader(
            ["+", "-"],
            value_parsers={any_section_option_matcher(key): str for key in ["caption", "comments", "+", "-"]},
        )
        return reader.read(self.config.study_path / "input" / "areas" / "sets.ini")
