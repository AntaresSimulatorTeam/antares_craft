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

from pathlib import Path

from antares.craft import ThematicTrimmingParameters


@pytest.fixture
def default_thematic_trimming_88() -> ThematicTrimmingParameters:
    return ThematicTrimmingParameters(
        psp_open_injection=True,
        psp_open_withdrawal=True,
        psp_open_level=True,
        psp_closed_injection=True,
        psp_closed_withdrawal=True,
        psp_closed_level=True,
        pondage_injection=True,
        pondage_withdrawal=True,
        pondage_level=True,
        battery_injection=True,
        battery_withdrawal=True,
        battery_level=True,
        other1_injection=True,
        other1_withdrawal=True,
        other1_level=True,
        other2_injection=True,
        other2_withdrawal=True,
        other2_level=True,
        other3_injection=True,
        other3_withdrawal=True,
        other3_level=True,
        other4_injection=True,
        other4_withdrawal=True,
        other4_level=True,
        other5_injection=True,
        other5_withdrawal=True,
        other5_level=True,
    )


@pytest.fixture
def xpansion_input_path() -> Path:
    return Path(__file__).parent / "assets" / "expansion_in.zip"

@pytest.fixture
def xpansion_output_path() -> Path:
    return Path(__file__).parent / "assets" / "expansion_out.zip"
