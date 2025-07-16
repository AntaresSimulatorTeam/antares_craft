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
import shutil

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.base_services import BaseXpansionService
from antares.craft.service.local_services.models.xpansion import serialize_xpansion_settings_local
from antares.craft.tools.serde_local.ini_writer import IniWriter


class XpansionLocalService(BaseXpansionService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self.study_name = study_name
        self._xpansion_path = self.config.study_path / "user" / "expansion"

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        raise NotImplementedError()

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        for folder in ["capa", "constraints", "weights"]:
            (self._xpansion_path / folder).mkdir(parents=True)
        with open(self._xpansion_path / "sensitivity" / "sensitivity.in", "w") as f:
            f.write("{}")
        (self._xpansion_path / "candidates.ini").touch()
        settings = XpansionSettings()
        ini_content = serialize_xpansion_settings_local(settings)
        IniWriter().write(ini_content, self._xpansion_path / "settings.ini")
        return XpansionConfiguration(self, settings)

    @override
    def delete(self) -> None:
        shutil.rmtree(self._xpansion_path)
