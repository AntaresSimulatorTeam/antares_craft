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
import shutil

from pathlib import Path

from antares.craft import create_study_local, read_study_local


class TestReadStudy:
    def test_directory_not_exists_error(self) -> None:
        current_dir = Path.cwd()
        study_path = current_dir / "fake_path"
        escaped_full_path = re.escape(str(study_path))

        with pytest.raises(FileNotFoundError, match=escaped_full_path):
            read_study_local(study_path)

    def test_directory_is_a_file(self, local_study):
        current_dir = local_study.service.config.study_path

        study_path = current_dir / "file.txt"
        study_path.touch()
        escaped_full_path = re.escape(str(study_path))

        with pytest.raises(FileNotFoundError, match=escaped_full_path):
            read_study_local(study_path)

    def test_read_outputs(self, local_study):
        """
        Ensures the reading methods doesn't fail when the output folder doesn't exist
        """
        study_path = Path(local_study.path)
        (study_path / "output").rmdir()
        read_study_local(study_path)

    def test_study_name(self, tmp_path: Path):
        """
        Ensures the reading area method isn't based on the name but on the study path
        """
        study_name = "name_inside_file"
        study = create_study_local(study_name, "880", tmp_path)
        study.create_area("fr")
        study_path = Path(study.path)
        new_path = study_path.parent / "other_name"
        shutil.move(study_path, new_path)
        study = read_study_local(new_path)
        assert len(study.get_areas()) == 1
