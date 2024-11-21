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

from pathlib import Path
from unittest.mock import patch

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
        call_counter = {"count": 0}

        def iterdir_side_effect(*args, **kwargs):
            call_counter["count"] += 1
            if call_counter["count"] == 2:
                raise PermissionError("Simulated exception on second is_dir call")
            return iter([])

        with caplog.at_level(logging.ERROR):
            with patch("pathlib.Path.is_dir", side_effect=iterdir_side_effect):
                with pytest.raises(PermissionError):
                    read_study_local(study_path)
                    assert any(
                        "PermissionError: Cannot access" in record.message for record in caplog.records
                    ), "Le message de logging attendu n'a pas été trouvé."

    def test_directory_exception(self, caplog, local_study_with_hydro):
        study_path = local_study_with_hydro.service.config.study_path

        # Compteur d'appels
        call_counter = {"count": 0}

        def iterdir_side_effect(*args, **kwargs):
            call_counter["count"] += 1
            if call_counter["count"] == 2:
                raise Exception("Simulated exception on second is_dir call")
            return iter([])

        with caplog.at_level(logging.ERROR):
            with patch("pathlib.Path.is_dir", side_effect=iterdir_side_effect):
                with pytest.raises(Exception):
                    read_study_local(study_path)
                    assert any(
                        "An error occurred with" in record.message
                        and "Simulated exception on second is_dir call" in record.message
                        for record in caplog.records
                    )
