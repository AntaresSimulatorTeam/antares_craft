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

from antares.craft import Study, read_study_local
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration


class TestXpansion:
    def test_create_and_read_basic_configuration(self, local_study_w_links: Study) -> None:
        # Asserts at first Xpansion is None.
        assert local_study_w_links.xpansion is None
        # Reading a study without an Xpansion configuration works. It returns None as an ` xpansion ` attribute.
        study_path = Path(local_study_w_links.path)
        study = read_study_local(study_path)
        assert study.xpansion is None

        # Create Xpansion configuration.
        xpansion = local_study_w_links.create_xpansion_configuration()
        assert isinstance(xpansion, XpansionConfiguration)
        assert xpansion.settings == XpansionSettings()
        assert xpansion.get_candidates() == {}
        assert xpansion.get_constraints() == {}
        assert xpansion.sensitivity is None

        # Asserts the reading works.
        xpansion_read = read_study_local(study_path).xpansion
        assert isinstance(xpansion_read, XpansionConfiguration)
        assert xpansion_read.settings == XpansionSettings()
        assert xpansion_read.get_candidates() == {}
        assert xpansion_read.get_constraints() == {}
        assert xpansion_read.sensitivity is None
