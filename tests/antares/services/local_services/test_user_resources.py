# Copyright (c) 2024-2026, RTE (https://www.rte-france.com)
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

from antares.craft import Study
from antares.craft.exceptions.exceptions import UserResourcesCreationError


def test_nominal_cases(local_study: Study) -> None:
    # Create a file at the root of the `user` folder
    local_study.add_user_resource("test.txt", b"Hello, world!")
    # Create a file inside an unexisting folder
    local_study.add_user_resource("folder/test.txt", b"John Doe")

    user_path = Path(local_study.path) / "user"
    assert (user_path / "test.txt").read_text() == "Hello, world!"
    assert (user_path / "folder" / "test.txt").read_text() == "John Doe"

    # Replace the existing file
    local_study.add_user_resource("test.txt", b"Goodbye, world!")
    assert (user_path / "test.txt").read_text() == "Goodbye, world!"


def test_error_cases(local_study: Study) -> None:
    # Transversal path
    with pytest.raises(UserResourcesCreationError, match="is not located in the user directory"):
        local_study.add_user_resource("../input/file.txt", b"Hello, world!")

    # Located inside the `expansion` folder
    with pytest.raises(UserResourcesCreationError, match="is located inside the expansion directory"):
        local_study.add_user_resource("expansion/settings.ini", b"Hello, world!")
