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
from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic_core import PydanticUseDefault


class LocalBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    @field_validator("*", mode="before")
    @classmethod
    def _usedefault_for_none(cls, value: Any) -> Any:
        """
        Will use the default value for the field if the value is None and the annotation doesn't allow for a None input.
        """
        if value is None:
            raise PydanticUseDefault()
        return value
