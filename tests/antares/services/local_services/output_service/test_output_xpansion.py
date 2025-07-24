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

import zipfile

from pathlib import Path

from antares.craft import Study
from antares.craft.model.output import (
    Output,
    XpansionResult,
)


class TestXpansionOutputReading:
    def _set_up(self, study: Study, resource: Path) -> Output:
        study_path = Path(study.path)
        # Put a real xpansion output inside the study and tests the reading method.
        with zipfile.ZipFile(resource, "r") as zf:
            zf.extractall(study_path / "output" / "xpansion_output")
        # Read the study
        study._read_outputs()
        return study.get_outputs().values().__iter__().__next__()

    def test_nominal_case(
        self, local_study: Study, xpansion_output_path: Path, xpansion_expected_output: XpansionResult
    ) -> None:
        output = self._set_up(local_study, xpansion_output_path)
        assert output.name == "xpansion_output"
        assert not output.archived

        result = output.get_xpansion_result()
        assert result == xpansion_expected_output
