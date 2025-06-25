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

from antares.craft import ConstraintTerm, FilterOption, LinkData, Study
from antares.craft.exceptions.exceptions import LinkDeletionError, MatrixFormatError, ReferencedObjectDeletionNotAllowed
from antares.craft.model.link import AssetType, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
from antares.craft.tools.serde_local.ini_reader import IniReader


class TestLink:
    def test_update_ui(self, local_study_w_links: Study) -> None:
        # Checks values before update
        link = local_study_w_links.get_links()["at / fr"]
        current_ui = LinkUi(colorr=1, link_width=29)
        assert link.ui == current_ui
        # Updates ui
        update_ui = LinkUiUpdate(link_width=4.2, colorg=255)
        new_ui = link.update_ui(update_ui)
        expected_ui = LinkUi(colorr=1, link_width=4.2, colorg=255)
        assert new_ui == expected_ui
        assert link.ui == expected_ui
        # Asserts the ini file is properly modified
        study_path = Path(local_study_w_links.path)
        ini_content = IniReader().read(study_path / "input" / "links" / link.area_from_id / "properties.ini")
        assert ini_content["fr"] == {
            "asset-type": "ac",
            "colorb": 112,
            "colorg": 255,
            "colorr": 1,
            "comments": "",
            "display-comments": True,
            "filter-synthesis": "weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "hurdles-cost": False,
            "link-style": "plain",
            "link-width": 4.2,
            "loop-flow": False,
            "transmission-capacities": "enabled",
            "use-phase-shifter": True,
        }

    def test_update_properties(self, local_study_w_links: Study) -> None:
        # Checks values before update
        link = local_study_w_links.get_links()["at / fr"]
        current_properties = LinkProperties(use_phase_shifter=True, filter_synthesis={FilterOption.WEEKLY})
        assert link.properties == current_properties
        # Updates properties
        update_properties = LinkPropertiesUpdate(use_phase_shifter=False, comments="new comment")
        new_properties = link.update_properties(update_properties)
        expected_properties = LinkProperties(
            use_phase_shifter=False, filter_synthesis={FilterOption.WEEKLY}, comments="new comment"
        )
        assert new_properties == expected_properties
        assert link.properties == expected_properties
        # Asserts the ini file is properly modified
        study_path = Path(local_study_w_links.path)
        ini_content = IniReader().read(study_path / "input" / "links" / link.area_from_id / "properties.ini")
        assert ini_content["fr"] == {
            "hurdles-cost": False,
            "loop-flow": False,
            "use-phase-shifter": False,
            "transmission-capacities": "enabled",
            "asset-type": "ac",
            "link-style": "plain",
            "link-width": 29,
            "colorr": 1,
            "colorg": 112,
            "colorb": 112,
            "display-comments": True,
            "filter-synthesis": "weekly",
            "filter-year-by-year": "annual, daily, hourly, monthly, weekly",
            "comments": "new comment",
        }

    def test_update_multiple_update_properties(self, local_study_w_links: Study) -> None:
        # Checks values before update
        link_at_fr = local_study_w_links.get_links()["at / fr"]
        link_fr_it = local_study_w_links.get_links()["fr / it"]
        link_at_it = local_study_w_links.get_links()["at / it"]
        current_properties = LinkProperties(use_phase_shifter=True, filter_synthesis={FilterOption.WEEKLY})
        assert link_at_fr.properties == current_properties
        assert link_fr_it.properties == current_properties
        assert link_at_it.properties == current_properties
        # Updates properties
        update_properties_at_fr = LinkPropertiesUpdate(hurdles_cost=True, comments="new comment")
        update_properties_fr_it = LinkPropertiesUpdate(use_phase_shifter=False, asset_type=AssetType.DC)
        body = {link_at_fr.id: update_properties_at_fr, link_fr_it.id: update_properties_fr_it}
        local_study_w_links.update_links(body)
        # Asserts links properties were modified
        assert link_at_fr.properties == LinkProperties(
            hurdles_cost=True, use_phase_shifter=True, filter_synthesis={FilterOption.WEEKLY}, comments="new comment"
        )
        assert link_fr_it.properties == LinkProperties(
            asset_type=AssetType.DC, filter_synthesis={FilterOption.WEEKLY}, use_phase_shifter=False
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
        study_path = Path(local_study_w_links.path)
        ini_content = IniReader().read(study_path / "input" / "links" / link.area_from_id / "properties.ini")
        assert "fr" not in ini_content

        with pytest.raises(LinkDeletionError, match=re.escape("Could not delete the link at / fr: it doesn't exist")):
            local_study_w_links.delete_link(link)

        # Recreate the link
        link = local_study_w_links.create_link(
            area_from="at",
            area_to="fr",
        )
        # Create a constraint referencing the link
        cluster_data = LinkData(area1="at", area2="fr")
        cluster_term = ConstraintTerm(data=cluster_data, weight=4.5, offset=3)
        local_study_w_links.create_binding_constraint(name="bc 1", terms=[cluster_term])

        # Ensures the link deletion fails
        with pytest.raises(
            ReferencedObjectDeletionNotAllowed,
            match="Link 'at / fr' is not allowed to be deleted, because it is referenced in the following binding constraints:\n1- 'bc 1'",
        ):
            local_study_w_links.delete_link(link)
