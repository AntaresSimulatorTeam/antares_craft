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

from typing import Any

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.base_services import BaseXpansionService
from antares.craft.service.local_services.models.xpansion import (
    parse_xpansion_candidate_local,
    parse_xpansion_constraints_local,
    parse_xpansion_sensitivity_local,
    parse_xpansion_settings_local,
    serialize_xpansion_settings_local,
)
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.json import from_json


class XpansionLocalService(BaseXpansionService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self.study_name = study_name
        self._xpansion_path = self.config.study_path / "user" / "expansion"

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        if not self._xpansion_path.exists():
            return None
        # Settings
        settings = parse_xpansion_settings_local(self._read_settings()["settings"])
        # Candidates
        candidates = {}
        ini_candidates = self._read_candidates()
        for values in ini_candidates.values():
            cdt = parse_xpansion_candidate_local(values)
            candidates[cdt.name] = cdt
        # Constraints
        constraints = {}
        file_name = settings.additional_constraints
        if file_name:
            constraints = parse_xpansion_constraints_local(self._read_constraints(file_name))
        # Sensitivity
        sensitivity = None
        sensitivity_content = self._read_sensitivity()
        if sensitivity_content:
            sensitivity = parse_xpansion_sensitivity_local(sensitivity_content)
        return XpansionConfiguration(
            self, settings=settings, candidates=candidates, constraints=constraints, sensitivity=sensitivity
        )

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        for folder in ["capa", "constraints", "weights", "sensitivity"]:
            (self._xpansion_path / folder).mkdir(parents=True)
        with open(self._xpansion_path / "sensitivity" / "sensitivity_in.json", "w") as f:
            f.write("{}")
        (self._xpansion_path / "candidates.ini").touch()
        settings = XpansionSettings()
        ini_content = serialize_xpansion_settings_local(settings)
        with open(self._xpansion_path / "settings.ini", "w") as f:
            f.writelines(f"{k}={v}\n" for k, v in ini_content.items())
        return XpansionConfiguration(self, settings)

    @override
    def delete(self) -> None:
        shutil.rmtree(self._xpansion_path)

    def _read_settings(self) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "settings.ini")

    def _read_candidates(self) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "candidates.ini")

    def _read_constraints(self, file_name: str) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "constraints" / file_name)

    def _read_sensitivity(self) -> dict[str, Any]:
        file_path = self._xpansion_path / "sensitivity" / "sensitivity_in.json"
        if file_path.exists():
            return from_json(file_path.read_text())
        return {}
