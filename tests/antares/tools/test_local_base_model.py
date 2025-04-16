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

from pydantic import Field

from antares.craft.service.local_services.models.base_model import LocalBaseModel


class LocalClass(LocalBaseModel):
    field_1: int = Field(default=1, alias="field-1")
    field_2: str = Field(default="char", alias="field-2")


def test_nominal_case():
    local_class = LocalClass.model_validate({"field_1": 2, "field_2": "double"})
    assert local_class.field_1 == 2
    assert local_class.field_2 == "double"

    local_class = LocalClass.model_validate({"field-1": 2, "field-2": "double"})
    assert local_class.field_1 == 2
    assert local_class.field_2 == "double"


def test_empty_fields():
    local_class = LocalClass.model_validate({})
    assert local_class.field_1 == 1
    assert local_class.field_2 == "char"


def test_fields_with_no_value():
    """
    The Simulator allows this format:

    [general]
    field_1 =
    field_2 = "var"

    And if we encounter this it will be considered as an empty string.
    If so, we'll have to consider it's the default value.
    """
    local_class = LocalClass.model_validate({"field_1": "", "field_2": "var"})
    assert local_class.field_1 == 1
    assert local_class.field_2 == "var"
