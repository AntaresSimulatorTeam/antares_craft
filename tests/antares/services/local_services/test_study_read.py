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

import logging
import re
from unittest import mock
from pathlib import Path
from antares.model.study import read_study_local

class TestReadStudy:
    def test_directory_not_exists_error(self, caplog):
        current_dir = Path.cwd()
        relative_path = Path("fake/path/")
        study_path = current_dir / relative_path
        escaped_full_path = re.escape(str(study_path))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match=escaped_full_path):
                read_study_local(study_path)

    def test_directory_permission_denied(self, caplog, local_study_with_hydro):
        study_path = local_study_with_hydro.service.config.study_path
        with caplog.at_level(logging.ERROR):
            with mock.patch(
                "pathlib.Path.iterdir",
                side_effect=PermissionError(f"Some content cannot be accessed in {local_study_with_hydro}"),
            ):
                with pytest.raises(
                    PermissionError,
                    match=f"Some content cannot be accessed in {local_study_with_hydro}",
                ):
                    read_study_local(study_path)
