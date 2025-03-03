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
from antares.craft.model.link import AssetType, LinkProperties, LinkPropertiesUpdate


class TestLink:
    def test_update_properties(self, tmp_path: Path, local_study_w_links: Study) -> None:
        # Checks values before update
        link = local_study_w_links.get_links()["at / fr"]
        current_properties = LinkProperties(hurdles_cost=False, asset_type=AssetType.AC)
        assert link.properties == current_properties
        # Updates properties
        update_properties = LinkPropertiesUpdate(hurdles_cost=True, comments="new comment")
        new_properties = link.update_properties(update_properties)
        expected_properties = LinkProperties(hurdles_cost=True, asset_type=AssetType.AC, comments="new comment")
        assert new_properties == expected_properties
        assert link.properties == expected_properties

    def test_matrices(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks all matrices exist and are empty
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        assert storage.get_pmax_injection().empty
        assert storage.get_pmax_withdrawal().empty
        assert storage.get_lower_rule_curve().empty
        assert storage.get_upper_rule_curve().empty
        assert storage.get_storage_inflows().empty

        # Replace matrices
        matrix = pd.DataFrame(data=8760 * [[3]])

        storage.update_pmax_injection(matrix)
        assert storage.get_pmax_injection().equals(matrix)

        storage.update_pmax_withdrawal(matrix)
        assert storage.get_pmax_withdrawal().equals(matrix)

        storage.update_lower_rule_curve(matrix)
        assert storage.get_lower_rule_curve().equals(matrix)

        storage.update_upper_rule_curve(matrix)
        assert storage.get_upper_rule_curve().equals(matrix)

        storage.update_storage_inflows(matrix)
        assert storage.get_storage_inflows().equals(matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for storage/fr/sts_1/pmax_injection matrix, expected shape is (8760, 1) and was : (2, 3)"
            ),
        ):
            storage.update_pmax_injection(matrix)
