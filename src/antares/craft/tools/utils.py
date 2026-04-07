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

"""
This file contains some utilities functions that we do not want to expose in the project documentation.
So they were moved outside the `model` package to keep it clean.
"""

from enum import Enum
from typing import Annotated, Any

from pydantic import BeforeValidator, PlainSerializer

from antares.craft.exceptions.exceptions import FilteringValueError
from antares.craft.model.commons import FilterOption


class ConstraintMatrixName(Enum):
    LESS_TERM = "lt"
    EQUAL_TERM = "eq"
    GREATER_TERM = "gt"


class STStorageMatrixName(Enum):
    PMAX_INJECTION = "pmax_injection"
    PMAX_WITHDRAWAL = "pmax_withdrawal"
    LOWER_CURVE_RULE = "lower_rule_curve"
    UPPER_RULE_CURVE = "upper_rule_curve"
    INFLOWS = "inflows"
    # NEW TS name v9.2
    COST_INJECTION = "cost_injection"
    COST_WITHDRAWAL = "cost_withdrawal"
    COST_LEVEL = "cost_level"
    COST_VARIATION_INJECTION = "cost_variation_injection"
    COST_VARIATION_WITHDRAWAL = "cost_variation_withdrawal"


class ThermalClusterMatrixName(Enum):
    PREPRO_DATA = "data"
    PREPRO_MODULATION = "modulation"
    SERIES = "series"
    SERIES_CO2_COST = "CO2Cost"
    SERIES_FUEL_COST = "fuelCost"


def validate_filters(filter_value: list[FilterOption] | str | None) -> list[FilterOption]:
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


def join_with_comma(values: set[Any] | None = None) -> str:
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
