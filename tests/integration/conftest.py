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

import pytest

from antares import create_study_local


@pytest.fixture
def other_study_with_other_area(tmp_path):
    other_study_name = "other test study"
    study_version = "880"

    # Study
    other_study = create_study_local(other_study_name, study_version, tmp_path.absolute())

    return other_study


@pytest.fixture
def unknown_area(other_study_with_other_area):
    usa = other_study_with_other_area.create_area("usa")
    return usa
