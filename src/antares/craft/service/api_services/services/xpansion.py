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
from antares.craft.exceptions.exceptions import APIError
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
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
            api_settings = self._wrapper.get(f"{self._expansion_url}/settings").json()
        except APIError:
            return None

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        raise NotImplementedError()
