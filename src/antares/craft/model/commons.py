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
from typing import Annotated, Optional, Union

from antares.craft.exceptions.exceptions import FilteringValueError
from pydantic import BeforeValidator, PlainSerializer


class FilterOption(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


def validate_filters(filter_value: Union[list[FilterOption], str]) -> list[FilterOption]:
    if isinstance(filter_value, str):
        filter_value = filter_value.strip()
        if not filter_value:
            return []

        valid_values = {str(e.value) for e in FilterOption}

        options = filter_value.replace(" ", "").split(",")

        invalid_options = [opt for opt in options if opt not in valid_values]
        if invalid_options:
            raise FilteringValueError(invalid_options, valid_values)
        options_enum: list[FilterOption] = list(dict.fromkeys(FilterOption(opt) for opt in options))
        return options_enum

    return filter_value


def join_with_comma(values: Optional[set[FilterOption]] = None) -> str:
    if values:
        return ", ".join(sorted(filtering.value for filtering in values))
    return ""


comma_separated_enum_set = Annotated[
    set[FilterOption],
    BeforeValidator(lambda x: validate_filters(x)),
    PlainSerializer(lambda x: join_with_comma(x)),
]

FILTER_VALUES: set[FilterOption] = {
    FilterOption.HOURLY,
    FilterOption.DAILY,
    FilterOption.WEEKLY,
    FilterOption.MONTHLY,
    FilterOption.ANNUAL,
}
