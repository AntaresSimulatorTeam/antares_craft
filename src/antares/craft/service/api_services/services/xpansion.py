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
from antares.craft.exceptions.exceptions import APIError, XpansionConfigurationCreationError
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.api_services.models.xpansion import parse_xpansion_settings_api
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
            return XpansionConfiguration(settings=settings, sensitivity=sensitivity)
        except APIError:
            return None
        # todo: here, we should add the reading for candidates and constraints.

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        try:
            self._wrapper.post(f"{self._expansion_url}/settings")
            settings, sensitivity = self._read_settings_and_sensitivity()
            return XpansionConfiguration(settings=settings, sensitivity=sensitivity)
        except APIError as e:
            raise XpansionConfigurationCreationError(self.study_id, e.message) from e

    def _read_settings_and_sensitivity(self) -> tuple[XpansionSettings, XpansionSensitivity | None]:
        api_settings = self._wrapper.get(f"{self._expansion_url}/settings").json()
        return parse_xpansion_settings_api(api_settings)
