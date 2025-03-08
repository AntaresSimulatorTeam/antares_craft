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

import numpy as np
import pandas as pd

from antares.craft import Study
from antares.craft.exceptions.exceptions import MatrixFormatError
from antares.craft.model.link import AssetType, LinkProperties, LinkPropertiesUpdate


class TestLink:
    def test_update_properties(self, local_study_w_links: Study) -> None:
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

    def test_update_multiple_update_properties(self, local_study_w_links: Study) -> None:
        # Checks values before update
        link_at_fr = local_study_w_links.get_links()["at / fr"]
        link_fr_it = local_study_w_links.get_links()["fr / it"]
        link_at_it = local_study_w_links.get_links()["at / it"]
        current_properties = LinkProperties(hurdles_cost=False, asset_type=AssetType.AC)
        assert link_at_fr.properties == current_properties
        assert link_fr_it.properties == current_properties
        assert link_at_it.properties == current_properties
        # Updates properties
        update_properties_at_fr = LinkPropertiesUpdate(hurdles_cost=True, comments="new comment")
        update_properties_fr_it = LinkPropertiesUpdate(use_phase_shifter=True, asset_type=AssetType.DC)
        body = {link_at_fr.id: update_properties_at_fr, link_fr_it.id: update_properties_fr_it}
        local_study_w_links.update_multiple_links(body)
        # Asserts links properties were modified
        assert link_at_fr.properties == LinkProperties(
            hurdles_cost=True, asset_type=AssetType.AC, comments="new comment"
        )
        assert link_fr_it.properties == LinkProperties(
            hurdles_cost=False, asset_type=AssetType.DC, use_phase_shifter=True
        )
        # Asserts links properties aren't updated as we didn't ask to
        assert link_at_it.properties == current_properties

    def test_matrices(self, local_study_w_links: Study) -> None:
        # Checks all matrices exist
        link = local_study_w_links.get_links()["at / fr"]
        link.get_parameters()
        link.get_capacity_direct()
        link.get_capacity_indirect()

        # Replace matrices
        matrix = pd.DataFrame(data=8760 * [[3]])
        link.update_capacity_direct(matrix)
        assert link.get_capacity_direct().equals(matrix)

        link.update_capacity_indirect(matrix)
        assert link.get_capacity_indirect().equals(matrix)

        parameters_matrix = pd.DataFrame(data=np.ones((8760, 6)))
        link.update_parameters(parameters_matrix)
        assert link.get_parameters().equals(parameters_matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for links/at/fr/links_parameters matrix, expected shape is (8760, 6) and was : (2, 3)"
            ),
        ):
            link.update_parameters(matrix)
