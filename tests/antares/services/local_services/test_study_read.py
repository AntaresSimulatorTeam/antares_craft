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

import re

from pathlib import Path

from antares.model.study import read_study_local


class TestReadStudy:
    def test_directory_not_exists_error(self):
        current_dir = Path.cwd()
        study_path = current_dir / "fake_path"
        escaped_full_path = re.escape(str(study_path))

        with pytest.raises(FileNotFoundError, match=escaped_full_path):
            read_study_local(study_path)

    def test_directory_is_a_file(self, local_study_with_hydro):
        current_dir = local_study_with_hydro.service.config.study_path

        study_path = current_dir / "file.txt"
        study_path.write_text("Not a directory")
        escaped_full_path = re.escape(str(study_path))

        with pytest.raises(FileNotFoundError, match=escaped_full_path):
            read_study_local(study_path)
