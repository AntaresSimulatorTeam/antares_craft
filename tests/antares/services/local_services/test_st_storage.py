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
from antares.craft.model.st_storage import STStorageProperties, STStoragePropertiesUpdate


class TestSTStorage:
    def test_update_properties(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks values before update
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        current_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
        assert storage.properties == current_properties
        # Updates properties
        update_properties = STStoragePropertiesUpdate(efficiency=0.1, reservoir_capacity=1.2)
        new_properties = storage.update_properties(update_properties)
        expected_properties = STStorageProperties(efficiency=0.1, initial_level_optim=True, reservoir_capacity=1.2)
        assert new_properties == expected_properties
        assert storage.properties == expected_properties
