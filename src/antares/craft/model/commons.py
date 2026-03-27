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
from typing import Annotated, Any, Optional

from pydantic import BeforeValidator, PlainSerializer

from antares.craft.exceptions.exceptions import FilteringValueError
from antares.study.version import StudyVersion

STUDY_VERSION_8_8 = StudyVersion.parse("8.8")
STUDY_VERSION_9_2 = StudyVersion.parse("9.2")
STUDY_VERSION_9_3 = StudyVersion.parse("9.3")


class FilterOption(Enum):
    """Enumeration of the available filter options for the output or the synthesis for example.

    This is case sensitive.
    
    Attributes:
        HOURLY: hourly filter
        DAILY: daily filter
        WEEKLY: weekly filter
        MONTHLY: monthly filter
        ANNUAL: annual filter
    """
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


def validate_filters(filter_value: list[FilterOption] | str | None) -> list[FilterOption]:
    """
    Validates and normalizes a set of filter options.

    This function accepts a list of `FilterOption` enums, a comma-separated string of filter values,
    or `None`. It validates the input, removes duplicates, and returns a list of valid `FilterOption` enums.

    Args:
        filter_value: The filter value(s) to validate. Can be:
            - A list of `FilterOption` enums.
            - A comma-separated string of filter values (e.g., "hourly, daily").
            - `None` or an empty string, which will return an empty list.

    Returns:
        list[FilterOption]: A list of unique, valid `FilterOption` enums. If the input is empty or invalid,
                            an empty list is returned.

    Raises:
        FilteringValueError: If any of the provided filter values are not valid `FilterOption` values.
    """
    if not filter_value:
        return []
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


def join_with_comma(values: Optional[set[Any]] = None) -> str:
    """
    Joins the string values of a set of enums (or other objects with a `value` attribute) into a comma-separated string.

    Args:
        values: A set of objects with a `value` attribute (e.g., enums). Defaults to `None`.

    Returns:
        str: A comma-separated string of the sorted values, or an empty string if the input is `None` or empty.
    """
    if values:
        return ", ".join(sorted(enum.value for enum in values))
    return ""


filtering_option = Annotated[
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
