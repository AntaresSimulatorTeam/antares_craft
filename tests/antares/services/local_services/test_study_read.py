import logging
import os
import time
from unittest import mock

from pathlib import Path
import pytest

from antares.config.local_configuration import LocalConfiguration
from antares.model.study import create_study_local, read_study_local



class TestReadStudy:

    def test_directory_not_exists_error(self, caplog):

        local_path = r"/fake/path/"
        study_name = "study_name"
        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match=f"Provided directory {local_path} does not exist."):
                read_study_local(study_name, "880", LocalConfiguration(local_path, study_name))

    def test_directory_permission_denied(self, tmp_path, caplog):
        # Given
        study_name = "studyTest"
        restricted_dir = tmp_path / study_name

        restricted_dir.mkdir(parents=True, exist_ok=True)
        restricted_path = restricted_dir / "file.txt"
        restricted_path.touch(exist_ok=True)
        with caplog.at_level(logging.ERROR):
            with mock.patch("pathlib.Path.iterdir",
                            side_effect=PermissionError(f"Some content cannot be accessed in {restricted_dir}")):
                escaped_path = str(restricted_dir).replace("\\", "\\\\")
                with pytest.raises(PermissionError, match=f"Some content cannot be accessed in {escaped_path}"):
                    read_study_local(study_name, "880", LocalConfiguration(tmp_path, study_name))
