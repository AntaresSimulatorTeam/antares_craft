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

import pandas as pd

from antares.craft import Study
from antares.craft.exceptions.exceptions import MatrixFormatError
from antares.craft.model.renewable import RenewableClusterProperties, RenewableClusterPropertiesUpdate


class TestRenewable:
    def test_update_properties(self, tmp_path: Path, local_study_with_renewable: Study) -> None:
        # Checks values before update
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        assert renewable.properties == RenewableClusterProperties(nominal_capacity=0)
        # Updates properties
        update_properties = RenewableClusterPropertiesUpdate(enabled=False, unit_count=3)
        new_properties = renewable.update_properties(update_properties)
        expected_properties = RenewableClusterProperties(enabled=False, unit_count=3, nominal_capacity=0)
        assert new_properties == expected_properties
        assert renewable.properties == expected_properties

    def test_matrices(self, tmp_path: Path, local_study_with_renewable: Study) -> None:
        # Checks all matrices exist and are empty
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        assert renewable.get_timeseries().empty

        # Replace matrix
        matrix = pd.DataFrame(data=8760 * [[3]])
        renewable.update_renewable_matrix(matrix)
        assert renewable.get_timeseries().equals(matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for renewable/fr/renewable cluster/renewable_series matrix, expected shape is (8760, Any) and was : (2, 3)"
            ),
        ):
            renewable.update_renewable_matrix(matrix)
