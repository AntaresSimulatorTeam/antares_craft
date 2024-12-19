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


def to_kebab(snake: str) -> str:
    """Convert a snake_case string to kebab-case

    Args:
        snake: The string to convert.

    Returns:
        The converted kebab-case string.
    """
    return snake.replace("_", "-")


def to_space(snake: str) -> str:
    """Convert a snake_case string to 'space case'

    Args:
        snake: The string to convert.

    Returns:
        The converted 'space case' string.
    """
    return snake.replace("_", " ")
