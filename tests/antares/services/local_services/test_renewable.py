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

from antares.craft import RenewableClusterGroup, Study, TimeSeriesInterpretation
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
        # Checks all matrices exist
        renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        renewable.get_timeseries()

        # Replace matrix
        matrix = pd.DataFrame(data=8760 * [[3]])
        renewable.set_series(matrix)
        assert renewable.get_timeseries().equals(matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for renewable/fr/renewable cluster/series matrix, expected shape is (8760, Any) and was : (2, 3)"
            ),
        ):
            renewable.set_series(matrix)

    def test_deletion(self, local_study_with_renewable):
        area_fr = local_study_with_renewable.get_areas()["fr"]
        renewable = area_fr.get_renewables()["renewable cluster"]
        area_fr.delete_renewable_clusters([renewable])
        # Asserts the area dict is empty
        assert area_fr.get_renewables() == {}
        # Asserts the file is empty
        ini_path = Path(local_study_with_renewable.path / "input" / "renewables" / "clusters" / "fr" / "list.ini")
        assert not ini_path.read_text()

    def test_update_renewable_properties(self, local_study_with_renewable):
        area_fr = local_study_with_renewable.get_areas()["fr"]
        renewable = area_fr.get_renewables()["renewable cluster"]
        update_for_renewable = RenewableClusterPropertiesUpdate(
            enabled=False, unit_count=13, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        dict_renewable = {renewable: update_for_renewable}
        local_study_with_renewable.update_renewable_clusters(dict_renewable)

        updated_renewable = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]

        # testing the modified value
        assert not updated_renewable.properties.enabled
        assert updated_renewable.properties.unit_count == 13
        assert updated_renewable.properties.ts_interpretation == TimeSeriesInterpretation.PRODUCTION_FACTOR

        # testing the unmodified value
        assert updated_renewable.properties.group == RenewableClusterGroup.OTHER1
