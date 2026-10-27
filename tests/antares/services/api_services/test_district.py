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

import pytest

import json

from typing import Any
from unittest.mock import patch

from requests import ConnectionError, Response

from antares.craft import APIconf, District, Study, read_study_api
from antares.craft.exceptions.exceptions import DistrictCreationError, DistrictDeletionError, DistrictsRetrievalError
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.service.api_services.factory import create_api_services

CONFIG = APIconf("http://127.0.0.1:8080", "")
URL = "http://127.0.0.1:8080/api/v1/studies/test"


def response(data: Any, status: int = 200) -> Response:
    result = Response()
    result.status_code = status
    result._content = json.dumps(data).encode()
    return result


def test_district_api_lifecycle() -> None:
    existing = {
        "id": "actual-id",
        "name": "Different caption",
        "areas": ["it", "fr"],
        "output": False,
        "comments": "Existing",
        "filterSynthesis": "hourly",
        "filterYearByYear": "daily",
    }
    body = {
        "metadata": {"name": "Test", "version": "10.2"},
        "areas": [],
        "links": [],
        "bindingConstraints": [],
        "districts": [existing],
    }
    first = {"id": "first district", "name": "First district", "output": False, "comments": "Test", "areas": []}
    second = {"id": "second", "name": "Second", "output": True, "comments": "", "areas": []}
    with (
        patch(
            "requests.Session.send",
            side_effect=[
                response(body),
                response([]),
                response(first),
                response(second),
                response([existing, first, second]),
                response(None),
            ],
        ) as send,
        patch("antares.craft.service.api_services.factory._read_settings", return_value=StudySettings()),
    ):
        study = read_study_api(CONFIG, "test")
        assert study.get_districts() == {"actual-id": District("Different caption", False, "Existing", ["fr", "it"])}
        created = study.create_districts([District("First district", False, "Test"), District("Second")])
        assert created == [District("First district", False, "Test"), District("Second")]
        assert study._district_service.read_districts([]) == study.get_districts()
        study.delete_district("first district")
        assert set(study.get_districts()) == {"actual-id", "second"}

    requests = [call.args[0] for call in send.call_args_list]
    assert [(request.method, request.url) for request in requests] == [
        ("GET", f"{URL}/data"),
        ("GET", f"{URL}/outputs"),
        ("POST", f"{URL}/districts"),
        ("POST", f"{URL}/districts"),
        ("GET", f"{URL}/districts"),
        ("DELETE", f"{URL}/districts/first%20district"),
    ]
    assert json.loads(requests[2].body) == {key: value for key, value in first.items() if key != "id"}
    assert json.loads(requests[3].body) == {key: value for key, value in second.items() if key != "id"}


@pytest.mark.parametrize("failure", [response({"description": "refused"}, 409), ConnectionError("offline")])
def test_partial_district_creation_keeps_successful_districts(failure: Response | ConnectionError) -> None:
    study = Study("Test", "10.2", create_api_services(CONFIG, "test"))
    first = {"id": "first", "name": "First", "output": True, "comments": "", "areas": []}
    with patch("requests.Session.send", side_effect=[response(first), failure]) as send:
        with pytest.raises(DistrictCreationError, match="Could not create the district 'Second'") as error:
            study.create_districts([District("First"), District("Second"), District("Third")])

    assert error.value.created_districts == [District("First")]
    assert study.get_districts() == {"first": District("First")}
    assert send.call_count == 2


def test_district_api_errors() -> None:
    study = Study("Test", "10.2", create_api_services(CONFIG, "test"))
    with patch("requests.Session.send", return_value=response({"description": "refused"}, 403)):
        with pytest.raises(DistrictsRetrievalError, match="refused"):
            study._district_service.read_districts([])
        with pytest.raises(DistrictDeletionError, match="refused"):
            study.delete_district("unknown")
    assert study.get_districts() == {}

    with patch("requests.Session.send", return_value=response([{"id": "incomplete", "name": "Incomplete"}])):
        with pytest.raises(DistrictsRetrievalError, match="validation errors"):
            study._district_service.read_districts([])


def test_missing_district_data_raises_retrieval_error() -> None:
    body = {
        "metadata": {"name": "Test", "version": "10.2"},
        "areas": [],
        "links": [],
        "bindingConstraints": [],
    }
    with (
        patch("requests.Session.send", return_value=response(body)),
        patch("antares.craft.service.api_services.factory._read_settings", return_value=StudySettings()),
    ):
        with pytest.raises(DistrictsRetrievalError, match="districts"):
            read_study_api(CONFIG, "test")
