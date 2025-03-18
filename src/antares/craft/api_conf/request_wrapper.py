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

import json

from typing import Any, Iterable, Mapping, Optional

import requests
import urllib3

from antares.craft.exceptions.exceptions import APIError

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
DATA_TYPE = Iterable[bytes] | str | bytes | list[tuple[Any, Any]] | tuple[tuple[Any, Any], ...] | Mapping[Any, Any]


def _handle_exceptions(response: requests.Response) -> requests.Response:
    """
    If an exception occurred, returns APIError exception containing the AntaresWeb error message.
    """
    if response.status_code - 200 < 100:
        return response
    try:
        msg = response.json()["description"]
    except (json.decoder.JSONDecodeError, KeyError):
        msg = response.reason
    raise APIError(msg)


class RequestWrapper:
    """
    A wrapper around the requests library
    """

    def __init__(self, session: requests.Session):
        self.session = session

    def get(self, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.get(url, **kwargs)
        return _handle_exceptions(response)

    def post(
        self, url: str, data: Optional[DATA_TYPE] = None, json: Optional[Any] = None, **kwargs: Any
    ) -> requests.Response:
        response = self.session.post(url, data, json, **kwargs)
        return _handle_exceptions(response)

    def put(self, url: str, data: Optional[DATA_TYPE] = None, **kwargs: Any) -> requests.Response:
        response = self.session.put(url, data, **kwargs)
        return _handle_exceptions(response)

    def patch(self, url: str, data: Optional[DATA_TYPE] = None, **kwargs: Any) -> requests.Response:
        response = self.session.patch(url, data, **kwargs)
        return _handle_exceptions(response)

    def delete(self, url: str, **kwargs: Any) -> requests.Response:
        response = self.session.delete(url, **kwargs)
        return _handle_exceptions(response)
