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

from antares.craft.config.base_configuration import BaseConfiguration
from antares.craft.exceptions.exceptions import MissingTokenError


class APIconf(BaseConfiguration):
    """Configuration for connecting to the Antares Web API.

    Attributes:
        api_host: Base URL of the Antares Web API (e.g. `https://antares-web.mydomain`).
        token: Bearer token used for authentication.
        verify: Whether to verify the server's TLS certificate. Defaults to `True`.

    Example:
        ```python
        api_config = APIconf(api_host="https://antares-web.mydomain", token="my-token")
        ```
    """

    def __init__(self, api_host: str, token: str, verify: bool = True) -> None:
        self._api_host: str = api_host
        self._token: str = token
        self._verify: bool = verify

    @property
    def token(self) -> str:
        """Bearer token used for API authentication."""
        return self._token

    @token.setter
    def token(self, value: str) -> None:
        """Set the bearer token.

        Args:
            value: New bearer token value.
        """
        self._token = value

    @property
    def verify(self) -> bool:
        """Whether TLS certificate verification is enabled."""
        return self._verify

    @property
    def api_host(self) -> str:
        return self._api_host

    @api_host.setter
    def api_host(self, value: str) -> None:
        """Base URL of the Antares Web API."""
        self._api_host = value

    def get_host(self) -> str:
        """Get the API host URL."""
        return self._api_host

    def get_token(self) -> str:
        """Return the authentication token.

        Returns:
            The bearer token used for API authentication.
        """
        return self._token

    def _checks_token(self) -> None:
        """Validates that a token is present for non-local API connections.

        Raises:
            MissingTokenError: If the API host is not local and no token is set.
        """
        if not self._is_launched_locally() and self._token is None:
            raise MissingTokenError()

    def _is_launched_locally(self) -> bool:
        """Checks whether the API host points to a local server.

        Returns:
            `True` if the host is `localhost` or `127.0.0.1`, `False` otherwise.
        """
        return self._api_host.startswith(("localhost", "http://127.0.0.1"))

    def set_up_api_conf(self) -> requests.Session:
        """Builds and returns a configured `requests.Session`.

        Validates the token, sets TLS verification, injects the `Authorization`
        header if a token is provided, and disables proxy settings for local connections.

        Returns:
            A `requests.Session` ready to make authenticated API calls.

        Raises:
            MissingTokenError: If the host is not local and no token has been set.
        """
        self._checks_token()
        session = requests.Session()
        session.verify = self._verify
        if self._token:
            token_bearer = f"Bearer {self._token}"
            session.headers.update({"Authorization": token_bearer})
        if self._is_launched_locally():
            session.trust_env = False  # disable proxy
        return session
