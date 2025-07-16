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


from antares.craft import Study
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration


class TestXpansion:
    def test_create_configuration(self, local_study_w_links: Study) -> None:
        assert local_study_w_links.xpansion is None

        xpansion = local_study_w_links.create_xpansion_configuration()
        assert isinstance(xpansion, XpansionConfiguration)
        assert xpansion.settings == XpansionSettings()
        assert xpansion.get_candidates() == {}
        assert xpansion.get_constraints() == {}
        assert xpansion.sensitivity is None
