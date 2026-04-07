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
