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

from antares.craft import STStorageGroup, Study
from antares.craft.exceptions.exceptions import MatrixFormatError
from antares.craft.model.st_storage import STStorageProperties, STStoragePropertiesUpdate
from antares.craft.service.local_services.models.st_storage import STStoragePropertiesLocal
from antares.study.version import StudyVersion


class TestSTStorage:
    def test_update_properties(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks values before update
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        current_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
        assert storage.properties == current_properties
        # Updates properties
        update_properties = STStoragePropertiesUpdate(efficiency=0.1, reservoir_capacity=1.2)
        new_properties = storage.update_properties(update_properties)
        expected_properties = STStorageProperties(
            group=STStorageGroup.OTHER1, efficiency=0.1, initial_level_optim=True, reservoir_capacity=1.2
        )
        assert new_properties == expected_properties
        assert storage.properties == expected_properties

    def test_update_properties_92(self, tmp_path: Path, local_study_92: Study) -> None:
        # Checks values before update
        local_study_92.get_areas()["fr"].create_st_storage("storage_local")
        storage = local_study_92.get_areas()["fr"].get_st_storages()["storage_local"]
        current_properties = STStorageProperties(
            efficiency_withdrawal=1, penalize_variation_injection=False, penalize_variation_withdrawal=False
        )
        assert storage.properties == current_properties
        # Updates properties
        update_properties = STStoragePropertiesUpdate(
            group="free_group",
            efficiency_withdrawal=0.4,
            penalize_variation_injection=True,
            penalize_variation_withdrawal=True,
        )
        new_properties = storage.update_properties(update_properties)
        expected_properties = STStorageProperties(
            group="free_group",
            efficiency_withdrawal=0.4,
            penalize_variation_injection=True,
            penalize_variation_withdrawal=True,
        )
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
        storage_1 = area_fr.get_st_storages()["sts_2"]
        area_fr.delete_st_storages([storage, storage_1])
        # Asserts the area dict is empty
        assert area_fr.get_st_storages() == {}
        # Asserts the file is empty
        ini_path = Path(local_study_w_storage.path / "input" / "st-storage" / "clusters" / "fr" / "list.ini")
        assert not ini_path.read_text()

    def test_st_storages_update_properties(self, local_study_w_storage):
        area_fr = local_study_w_storage.get_areas()["fr"]
        storage = area_fr.get_st_storages()["sts_1"]
        storage_1 = area_fr.get_st_storages()["sts_2"]
        update_for_storage = STStoragePropertiesUpdate(enabled=False, group=STStorageGroup.PSP_CLOSED)
        update_for_storage_1 = STStoragePropertiesUpdate(group=STStorageGroup.PONDAGE, injection_nominal_capacity=1000)
        dict_storage = {storage: update_for_storage, storage_1: update_for_storage_1}
        local_study_w_storage.update_st_storages(dict_storage)

        # testing the modified value
        assert not storage.properties.enabled
        assert storage.properties.group == STStorageGroup.PSP_CLOSED
        # testing the unmodified value
        assert storage.properties.efficiency == 0.4

        # testing the modified value
        assert storage_1.properties.group == STStorageGroup.PONDAGE
        assert storage_1.properties.injection_nominal_capacity == 1000
        # testing the unmodified value
        assert storage_1.properties.enabled
        assert storage_1.properties.initial_level == 0.5

    def test_storage_group_version_handling(self):
        properties_88 = STStorageProperties(
            enabled=True,
            group=STStorageGroup.BATTERY,
            injection_nominal_capacity=100,
            withdrawal_nominal_capacity=200,
            reservoir_capacity=1000,
        )

        local_88 = STStoragePropertiesLocal.from_user_model(properties_88, StudyVersion.parse("8.8"))

        assert local_88.group == STStorageGroup.BATTERY
        assert isinstance(local_88.group, STStorageGroup)

        back_to_user_88 = local_88.to_user_model()
        assert back_to_user_88.group == STStorageGroup.BATTERY

        properties_88_no_group = STStorageProperties(
            enabled=True, injection_nominal_capacity=100, withdrawal_nominal_capacity=200, reservoir_capacity=1000
        )

        local_88_no_group = STStoragePropertiesLocal.from_user_model(properties_88_no_group, StudyVersion.parse("8.8"))

        assert local_88_no_group.group == STStorageGroup.OTHER1
        assert isinstance(local_88_no_group.group, STStorageGroup)

        properties_92 = STStorageProperties(
            enabled=True,
            group="custom_group",
            injection_nominal_capacity=100,
            withdrawal_nominal_capacity=200,
            reservoir_capacity=1000,
        )

        local_92 = STStoragePropertiesLocal.from_user_model(properties_92, StudyVersion.parse("9.2"))

        assert local_92.group == "custom_group"
        assert isinstance(local_92.group, str)

        back_to_user_92 = local_92.to_user_model()
        assert back_to_user_92.group == "custom_group"

        properties_92_no_group = STStorageProperties(
            enabled=True, injection_nominal_capacity=100, withdrawal_nominal_capacity=200, reservoir_capacity=1000
        )

        local_92_no_group = STStoragePropertiesLocal.from_user_model(properties_92_no_group, StudyVersion.parse("9.2"))

        assert local_92_no_group.group == ""
        assert isinstance(local_92_no_group.group, str)
