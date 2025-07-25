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

from antares.craft.service.api_services.models.base_model import APIBaseModel


class TestModel(APIBaseModel):
    test: int


def test_extra_fields_are_permitted() -> None:
    data = {"test": 1, "extra": 2}
    model = TestModel(**data)
    assert model.test == 1
    assert model.__pydantic_extra__ is not None and model.__pydantic_extra__["extra"] == 2
