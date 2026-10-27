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

from dataclasses import dataclass, field


@dataclass(frozen=True)
class District:
    """Represents a spatial aggregate of study areas.

    Attributes:
        name: Name of the district.
        output: Whether to generate simulation outputs for the district.
        comments: Description of the district.
        areas: Identifiers of the areas belonging to the district.
    """

    name: str
    output: bool = True
    comments: str = ""
    areas: list[str] = field(default_factory=list)
