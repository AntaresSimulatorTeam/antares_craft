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

from enum import Enum
from typing import List, Set


class FilterOption(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


def sort_filter_values(filter_options: Set[FilterOption]) -> List[str]:
    filter_defaults = ["hourly", "daily", "weekly", "monthly", "annual"]
    filter_values = [filter_option.value for filter_option in filter_options]
    return sorted(filter_values, key=lambda x: filter_defaults.index(x))
