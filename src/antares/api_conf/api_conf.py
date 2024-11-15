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

import requests

from antares.config.base_configuration import BaseConfiguration
from antares.exceptions.exceptions import MissingTokenError


class APIconf(BaseConfiguration):
    """
    APIconf defines host and token to be used for API mode
    """

    def __init__(self, api_host: str, token: str, verify: bool = True) -> None:
        self._api_host: str = api_host
        self._token: str = token
        self._verify: bool = verify

    @property
    def token(self) -> str:
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        self._token = value

    @property
    def verify(self) -> bool:
        return self._verify

    @property
    def api_host(self) -> str:
        return self._api_host

    @api_host.setter
    def api_host(self, value: str) -> None:
        self._api_host = value

    def get_host(self) -> str:
        return self._api_host

    def get_token(self) -> str:
        return self._token

    def checks_token(self) -> None:
        if self._api_host not in ["localhost", "127.0.0.1"] and self._token is None:
            raise MissingTokenError()

    def set_up_api_conf(self) -> requests.Session:
        self.checks_token()
        session = requests.Session()
        session.verify = self._verify
        if self._token:
            token_bearer = f"Bearer {self._token}"
            session.headers.update({"Authorization": token_bearer})
        return session
