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

import re

from enum import Enum
from typing import Optional

from typing_extensions import override

# Invalid chars was taken from Antares Simulator (C++).
_sub_invalid_chars = re.compile(r"[^a-zA-Z0-9_(),& -]+").sub


def transform_name_to_id(name: str) -> str:
    """
    Transform a name into an identifier.
    This method is used in AntaresWeb to construct their ids.
    """
    return _sub_invalid_chars(" ", name).strip().lower()


class EnumIgnoreCase(Enum):
    @classmethod
    @override
    def _missing_(cls, value: object) -> Optional["EnumIgnoreCase"]:
        if isinstance(value, str):
            for member in cls:
                if member.value.upper() == value.upper():
                    return member
        return None
