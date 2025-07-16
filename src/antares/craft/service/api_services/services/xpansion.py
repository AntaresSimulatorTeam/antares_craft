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
from typing_extensions import override

from antares.craft import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    XpansionConfigurationCreationError,
    XpansionConfigurationDeletionError,
    XpansionConfigurationReadingError,
)
from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.api_services.models.xpansion import (
    parse_xpansion_candidate_api,
    parse_xpansion_constraints_api,
    parse_xpansion_settings_api,
)
from antares.craft.service.base_services import BaseXpansionService


class XpansionAPIService(BaseXpansionService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())
        self._expansion_url = f"{self.config.get_host()}/api/v1/studies/{study_id}/extensions/xpansion"

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        # Checks the settings. If we have a 404 Exception, it means we don't have any Xpansion configuration
        try:
            settings, sensitivity = self._read_settings_and_sensitivity()
        except APIError:
            return None
        try:
            # Candidates
            candidates = self._read_candidates()
            # Constraints
            constraints = {}
            if settings.additional_constraints:
                constraints = self._read_constraints(settings.additional_constraints)
            return XpansionConfiguration(
                xpansion_service=self,
                settings=settings,
                sensitivity=sensitivity,
                candidates=candidates,
                constraints=constraints,
            )
        except APIError as e:
            raise XpansionConfigurationReadingError(self.study_id, e.message) from e

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        try:
            self._wrapper.post(f"{self._expansion_url}/settings")
            settings, sensitivity = self._read_settings_and_sensitivity()
            return XpansionConfiguration(xpansion_service=self, settings=settings, sensitivity=sensitivity)
        except APIError as e:
            raise XpansionConfigurationCreationError(self.study_id, e.message) from e

    @override
    def delete(self) -> None:
        try:
            self._wrapper.delete(self._expansion_url)
        except APIError as e:
            raise XpansionConfigurationDeletionError(self.study_id, e.message) from e

    def _read_settings_and_sensitivity(self) -> tuple[XpansionSettings, XpansionSensitivity | None]:
        api_settings = self._wrapper.get(f"{self._expansion_url}/settings").json()
        return parse_xpansion_settings_api(api_settings)

    def _read_candidates(self) -> dict[str, XpansionCandidate]:
        candidates_api = self._wrapper.get(f"{self._expansion_url}/candidates").json()
        candidates = {}
        for cdt_api in candidates_api:
            cdt = parse_xpansion_candidate_api(cdt_api)
            candidates[cdt.name] = cdt
        return candidates

    def _read_constraints(self, file_name: str) -> dict[str, XpansionConstraint]:
        constraints_api = self._wrapper.get(f"{self._expansion_url}/resources/constraints/{file_name}").json()
        return parse_xpansion_constraints_api(constraints_api)
