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


from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, OutputsRetrievalError
from antares.craft.model.output import Output
from antares.craft.service.base_services import BaseOutputService


class OutputApiService(BaseOutputService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    def read_outputs(self) -> list[Output]:
        url = f"{self._base_url}/studies/{self.study_id}/outputs"
        try:
            response = self._wrapper.get(url)
            outputs_json_list = response.json()
            return [Output(name=output["name"], archived=output["archived"]) for output in outputs_json_list]
        except APIError as e:
            raise OutputsRetrievalError(self.study_id, e.message)
