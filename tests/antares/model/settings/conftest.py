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

from antares.craft.model.settings.playlist_parameters import PlaylistData, PlaylistParameters


@pytest.fixture
def test_playlist() -> PlaylistParameters:
    return PlaylistParameters(playlist=[PlaylistData(status=False, weight=2.1)])


@pytest.fixture
def test_playlist_model_dump(test_playlist) -> dict[str, str]:
    return test_playlist.model_dump()
