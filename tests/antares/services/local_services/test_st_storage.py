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

import copy
import re

from pathlib import Path

import pandas as pd

from checksumdir import dirhash

from antares.craft import STStorageGroup, Study
from antares.craft.exceptions.exceptions import (
    InvalidFieldForVersionError,
    MatrixFormatError,
    STStoragePropertiesUpdateError,
)
from antares.craft.model.st_storage import STStorageProperties, STStoragePropertiesUpdate
from antares.craft.model.study import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antares.craft.service.local_services.models.st_storage import (
    parse_st_storage_local,
    serialize_st_storage_local,
)


class TestSTStorage:
    def test_update_properties(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks values before update
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        current_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
        assert storage.properties == current_properties
        # Updates properties
        update_properties = STStoragePropertiesUpdate(efficiency=0.1, reservoir_capacity=1.2)
        new_properties = storage.update_properties(update_properties)

        assert new_properties.efficiency == 0.1
        assert new_properties.reservoir_capacity == 1.2
        assert new_properties.initial_level_optim is True

    def test_update_properties_88_error(self, tmp_path: Path, local_study_w_storage: Study) -> None:
        # Checks values before update
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        current_properties = STStorageProperties(efficiency=0.4, initial_level_optim=True)
        assert storage.properties == current_properties
        # Updates properties
        update_properties = STStoragePropertiesUpdate(
            efficiency=0.1, reservoir_capacity=1.2, penalize_variation_withdrawal=True
        )
        with pytest.raises(
            InvalidFieldForVersionError,
            match="Field penalize_variation_withdrawal is not a valid field for study version 8.8",
        ):
            storage.update_properties(update_properties)

    def test_update_properties_92(self, tmp_path: Path, local_study_92: Study) -> None:
        local_study_92.get_areas()["fr"].create_st_storage("storage_local")
        storage = local_study_92.get_areas()["fr"].get_st_storages()["storage_local"]

        # Update properties with some fields set
        update_properties = STStoragePropertiesUpdate(
            group="free_group",
            efficiency_withdrawal=6.4,
            penalize_variation_injection=True,
            penalize_variation_withdrawal=True,
        )
        new_properties = storage.update_properties(update_properties)

        # Check only the updated fields have the expected values
        assert new_properties.group == "free_group"
        assert new_properties.efficiency_withdrawal == 6.4
        assert new_properties.penalize_variation_injection is True
        assert new_properties.penalize_variation_withdrawal is True

        # Also check storage properties reflect those updates
        assert storage.properties.group == "free_group"
        assert storage.properties.efficiency_withdrawal == 6.4
        assert storage.properties.penalize_variation_injection is True
        assert storage.properties.penalize_variation_withdrawal is True

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

    def test_deletion(self, local_study_w_storage: Study) -> None:
        area_fr = local_study_w_storage.get_areas()["fr"]
        storage = area_fr.get_st_storages()["sts_1"]
        storage_1 = area_fr.get_st_storages()["sts_2"]
        area_fr.delete_st_storages([storage, storage_1])
        # Asserts the area dict is empty
        assert area_fr.get_st_storages() == {}
        # Asserts the file is empty
        ini_path = Path(local_study_w_storage.path / "input" / "st-storage" / "clusters" / "fr" / "list.ini")
        assert not ini_path.read_text()

    def test_st_storages_update_properties(self, local_study_w_storage: Study) -> None:
        area_fr = local_study_w_storage.get_areas()["fr"]
        storage = area_fr.get_st_storages()["sts_1"]
        storage_1 = area_fr.get_st_storages()["sts_2"]
        update_for_storage = STStoragePropertiesUpdate(enabled=False, group=STStorageGroup.PSP_CLOSED.value)
        update_for_storage_1 = STStoragePropertiesUpdate(
            group=STStorageGroup.PONDAGE.value, injection_nominal_capacity=1000
        )
        dict_storage = {storage: update_for_storage, storage_1: update_for_storage_1}
        local_study_w_storage.update_st_storages(dict_storage)

        assert not storage.properties.enabled
        assert storage.properties.group == STStorageGroup.PSP_CLOSED.value

        assert storage.properties.efficiency == 0.4

        assert storage_1.properties.group == STStorageGroup.PONDAGE.value
        assert storage_1.properties.injection_nominal_capacity == 1000

        assert storage_1.properties.enabled
        assert storage_1.properties.initial_level == 0.5

    def test_storage_group_version_handling(self) -> None:
        properties_88 = STStorageProperties(
            enabled=True,
            group=STStorageGroup.BATTERY.value,
            injection_nominal_capacity=100,
            withdrawal_nominal_capacity=200,
            reservoir_capacity=1000,
        )

        # Round trip
        local_88 = serialize_st_storage_local(STUDY_VERSION_8_8, properties_88)
        assert local_88["group"] == STStorageGroup.BATTERY.value
        user_88 = parse_st_storage_local(STUDY_VERSION_8_8, local_88)
        assert user_88.group == STStorageGroup.BATTERY.value

        properties_88_no_group = STStorageProperties(
            enabled=True, injection_nominal_capacity=100, withdrawal_nominal_capacity=200, reservoir_capacity=1000
        )
        # Round trip
        local_88_no_group = serialize_st_storage_local(STUDY_VERSION_8_8, properties_88_no_group)
        assert local_88_no_group["group"] == STStorageGroup.OTHER1.value
        user_88_no_group = parse_st_storage_local(STUDY_VERSION_8_8, local_88_no_group)
        assert user_88_no_group.group == STStorageGroup.OTHER1.value

        properties_92 = STStorageProperties(
            enabled=True,
            group="custom_group",
            injection_nominal_capacity=100,
            withdrawal_nominal_capacity=200,
            reservoir_capacity=1000,
        )

        # Round trip
        local_92 = serialize_st_storage_local(STUDY_VERSION_9_2, properties_92)
        assert local_92["group"] == "custom_group"
        back_to_user_92 = parse_st_storage_local(STUDY_VERSION_9_2, local_92)
        assert back_to_user_92.group == "custom_group"

        # Round trip
        properties_92_no_group = STStorageProperties(
            enabled=True, injection_nominal_capacity=100, withdrawal_nominal_capacity=200, reservoir_capacity=1000
        )
        local_92_no_group = serialize_st_storage_local(STUDY_VERSION_9_2, properties_92_no_group)
        assert local_92_no_group["group"] == STStorageGroup.OTHER1.value

    def test_update_several_properties_fails(self, local_study_w_storage: Study) -> None:
        """
        Ensures the update fails as the area doesn't exist.
        We also want to ensure the study wasn't partially modified.
        """
        update_for_storage = STStoragePropertiesUpdate(enabled=False, efficiency=0.6)
        storage = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
        fake_storage = copy.deepcopy(storage)
        fake_storage._area_id = "fake"
        dict_storage = {storage: update_for_storage, fake_storage: update_for_storage}
        storage_folder = Path(local_study_w_storage.path) / "input" / "st-storage"
        hash_before_update = dirhash(storage_folder, "md5")
        with pytest.raises(
            STStoragePropertiesUpdateError,
            match=re.escape(
                "Could not update properties for short term storage 'sts_1' inside area 'fake': The storage does not exist"
            ),
        ):
            local_study_w_storage.update_st_storages(dict_storage)
        hash_after_update = dirhash(storage_folder, "md5")
        assert hash_before_update == hash_after_update

    def test_errors_inside_properties_values(self, local_study_92: Study) -> None:
        area = local_study_92.get_areas()["fr"]

        for field in [
            "injection_nominal_capacity",
            "withdrawal_nominal_capacity",
            "reservoir_capacity",
            "efficiency",
            "efficiency_withdrawal",
        ]:
            with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
                area.create_st_storage("sts", properties=STStorageProperties(**{field: -2}))

        with pytest.raises(ValueError, match=re.escape("efficiency_withdrawal must be greater than efficiency")):
            area.create_st_storage("sts", properties=STStorageProperties(efficiency_withdrawal=0.4))

        storage = area.create_st_storage("sts")
        with pytest.raises(ValueError, match=re.escape("efficiency_withdrawal must be greater than efficiency")):
            storage.update_properties(STStoragePropertiesUpdate(efficiency=4))
