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


from pathlib import Path

from antares.craft import Study
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

    def test_matrices(self, tmp_path: Path, local_study_w_links: Study) -> None:
        # Checks all matrices exist and are empty
        link = local_study_w_links.get_links()["at / fr"]
        assert link.get_parameters().empty
        assert link.get_capacity_direct().empty
        assert link.get_capacity_indirect().empty

        # Replace matrices
        # todo
