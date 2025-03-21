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

import numpy as np
import pandas as pd

from antares.craft import Study
from antares.craft.exceptions.exceptions import LinkDeletionError, MatrixFormatError
from antares.craft.model.link import AssetType, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


class TestLink:
    def test_update_ui(self, local_study_w_links: Study) -> None:
        # Checks values before update
        link = local_study_w_links.get_links()["at / fr"]
        current_ui = LinkUi()
        assert link.ui == current_ui
        # Updates ui
        update_ui = LinkUiUpdate(link_width=4.2, colorg=255)
        new_ui = link.update_ui(update_ui)
        expected_ui = LinkUi(link_width=4.2, colorg=255)
        assert new_ui == expected_ui
        assert link.ui == expected_ui
        # Asserts the ini file is properly modified
        ini_file = IniFile(
            Path(local_study_w_links.path), InitializationFilesTypes.LINK_PROPERTIES_INI, link.area_from_id
        )
        assert ini_file.ini_dict["fr"] == {
            "asset-type": "ac",
            "colorb": "112",
            "colorg": "255",
            "colorr": "112",
            "comments": "",
            "display-comments": "True",
            "filter-synthesis": "annual, daily, hourly, monthly, weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "hurdles-cost": "False",
            "link-style": "plain",
            "link-width": "4.2",
            "loop-flow": "False",
            "transmission-capacities": "enabled",
            "use-phase-shifter": "False",
        }

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
        # Asserts the ini file is properly modified
        ini_file = IniFile(
            Path(local_study_w_links.path), InitializationFilesTypes.LINK_PROPERTIES_INI, link.area_from_id
        )
        assert ini_file.ini_dict["fr"] == {
            "hurdles-cost": "True",
            "loop-flow": "False",
            "use-phase-shifter": "False",
            "transmission-capacities": "enabled",
            "asset-type": "ac",
            "link-style": "plain",
            "link-width": "1.0",
            "colorr": "112",
            "colorg": "112",
            "colorb": "112",
            "display-comments": "True",
            "filter-synthesis": "annual, daily, hourly, monthly, weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "comments": "new comment",
        }

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
        local_study_w_links.update_links(body)
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
        link.set_capacity_direct(matrix)
        assert link.get_capacity_direct().equals(matrix)

        link.set_capacity_indirect(matrix)
        assert link.get_capacity_indirect().equals(matrix)

        parameters_matrix = pd.DataFrame(data=np.ones((8760, 6)))
        link.set_parameters(parameters_matrix)
        assert link.get_parameters().equals(parameters_matrix)

        # Try to update with wrongly formatted matrix
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for links/at/fr/links_parameters matrix, expected shape is (8760, 6) and was : (2, 3)"
            ),
        ):
            link.set_parameters(matrix)

    def test_deletion(self, local_study_w_links: Study) -> None:
        link = local_study_w_links.get_links()["at / fr"]
        local_study_w_links.delete_link(link)
        ini_file = IniFile(
            Path(local_study_w_links.path), InitializationFilesTypes.LINK_PROPERTIES_INI, link.area_from_id
        )
        assert "fr" not in ini_file.ini_dict

        with pytest.raises(LinkDeletionError, match=re.escape("Could not delete the link at / fr: it doesn't exist")):
            local_study_w_links.delete_link(link)
