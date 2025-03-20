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

    def test_matrices(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks all matrices exist
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        storage.get_pmax_injection()
        storage.get_pmax_withdrawal()
        storage.get_lower_rule_curve()
        storage.get_upper_rule_curve()
        storage.get_storage_inflows()

        # Replace matrices
        matrix = pd.DataFrame(data=8760 * [[3]])

        storage.update_pmax_injection(matrix)
        assert storage.get_pmax_injection().equals(matrix)

        storage.set_pmax_withdrawal(matrix)
        assert storage.get_pmax_withdrawal().equals(matrix)

        storage.set_lower_rule_curve(matrix)
        assert storage.get_lower_rule_curve().equals(matrix)

        storage.set_upper_rule_curve(matrix)
        assert storage.get_upper_rule_curve().equals(matrix)

        storage.set_storage_inflows(matrix)
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

    def test_deletion(self, local_study_w_storage):
        area_fr = local_study_w_storage.get_areas()["fr"]
        storage = area_fr.get_st_storages()["sts_1"]
        area_fr.delete_st_storages([storage])
        # Asserts the area dict is empty
        assert area_fr.get_st_storages() == {}
        # Asserts the file is empty
        ini_path = Path(local_study_w_storage.path / "input" / "st-storage" / "clusters" / "fr" / "list.ini")
        assert not ini_path.read_text()
