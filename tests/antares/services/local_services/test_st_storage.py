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

import numpy as np
import pandas as pd

from checksumdir import dirhash

from antares.craft import STStorageAdditionalConstraintUpdate, STStorageGroup, Study, read_study_local
from antares.craft.exceptions.exceptions import (
    InvalidFieldForVersionError,
    MatrixFormatError,
    STStoragePropertiesUpdateError,
)
from antares.craft.model.st_storage import (
    AdditionalConstraintOperator,
    AdditionalConstraintVariable,
    Occurrence,
    STStorageAdditionalConstraint,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.model.study import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antares.craft.service.local_services.models.st_storage import (
    parse_st_storage_local,
    serialize_st_storage_local,
)
from antares.craft.tools.serde_local.ini_reader import IniReader


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
        sts_folder = Path(local_study_w_storage.path) / "input" / "st-storage"
        assert not (sts_folder / "clusters" / "fr" / "list.ini").read_text()
        # Asserts the series do not exist anymore
        assert not (sts_folder / "series" / "fr" / "sts_1").exists()
        assert not (sts_folder / "series" / "fr" / "sts_2").exists()

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
            "initial_level",
        ]:
            with pytest.raises(ValueError, match="Input should be greater than or equal to 0"):
                area.create_st_storage("sts", properties=STStorageProperties(**{field: -2}))  # type: ignore

        with pytest.raises(
            ValueError, match=re.escape("efficiency must be lower than efficiency_withdrawal. Currently: 1.0 > 0.4")
        ):
            area.create_st_storage("sts", properties=STStorageProperties(efficiency_withdrawal=0.4))

        storage = area.create_st_storage("sts")
        with pytest.raises(
            ValueError, match=re.escape("efficiency must be lower than efficiency_withdrawal. Currently: 4.0 > 1")
        ):
            storage.update_properties(STStoragePropertiesUpdate(efficiency=4))


##########################
# Additional constraints part
##########################


def test_nominal_case_additional_constraints(local_study_92: Study) -> None:
    area_fr = local_study_92.get_areas()["fr"]
    sts = area_fr.create_st_storage("sts_1")
    # Ensures no constraint exists
    assert sts.get_constraints() == {}
    # Ensures we're able to read the study
    study_path = Path(local_study_92.path)
    study = read_study_local(study_path)
    sts = study.get_areas()["fr"].get_st_storages()["sts_1"]
    assert sts.get_constraints() == {}
    # Create several constraints
    constraints_fr = [
        STStorageAdditionalConstraint(name="constraint_1", enabled=False),
        STStorageAdditionalConstraint(
            name="Constraint2??", variable=AdditionalConstraintVariable.WITHDRAWAL, occurrences=[Occurrence([167, 168])]
        ),
    ]
    sts.create_constraints(constraints_fr)
    # Ensures the reading method succeeds
    study = read_study_local(study_path)
    sts = study.get_areas()["fr"].get_st_storages()["sts_1"]
    assert sts.get_constraints() == {
        "constraint_1": STStorageAdditionalConstraint(
            name="constraint_1",
            variable=AdditionalConstraintVariable.NETTING,
            operator=AdditionalConstraintOperator.LESS,
            occurrences=[],
            enabled=False,
        ),
        "constraint2": STStorageAdditionalConstraint(
            name="Constraint2??",
            variable=AdditionalConstraintVariable.WITHDRAWAL,
            operator=AdditionalConstraintOperator.LESS,
            occurrences=[Occurrence(hours=[167, 168])],
            enabled=True,
        ),
    }

    # Update one constraint
    new_constraint = sts.update_constraint(
        "constraint2",
        STStorageAdditionalConstraintUpdate(
            variable=AdditionalConstraintVariable.NETTING,
            operator=AdditionalConstraintOperator.GREATER,
        ),
    )
    assert new_constraint == STStorageAdditionalConstraint(
        name="Constraint2??",
        variable=AdditionalConstraintVariable.NETTING,
        operator=AdditionalConstraintOperator.GREATER,
        occurrences=[Occurrence(hours=[167, 168])],
        enabled=True,
    )

    # Checks ini content
    ini_path = study_path / "input" / "st-storage" / "constraints" / "fr" / "sts_1" / "additional-constraints.ini"
    content = IniReader().read(ini_path)
    assert content == {
        "Constraint2??": {
            "enabled": True,
            "hours": "[167, 168]",
            "name": "Constraint2??",
            "operator": "greater",
            "variable": "netting",
        },
        "constraint_1": {
            "enabled": False,
            "hours": "[]",
            "name": "constraint_1",
            "operator": "less",
            "variable": "netting",
        },
    }

    # Deletes a constraint
    sts.delete_constraints(["constraint_1"])
    constraints = sts.get_constraints()
    assert len(constraints) == 1
    assert "constraint_1" not in constraints
    assert not (ini_path.parent / "rhs_constraint1.txt").exists()

    # Checks ini content
    content = IniReader().read(ini_path)
    assert content == {
        "Constraint2??": {
            "enabled": True,
            "hours": "[167, 168]",
            "name": "Constraint2??",
            "operator": "greater",
            "variable": "netting",
        }
    }

    # Add another constraint
    sts.create_constraints(
        [STStorageAdditionalConstraint(name="Constraint3", operator=AdditionalConstraintOperator.EQUAL)]
    )
    assert sts.get_constraints()["constraint3"] == STStorageAdditionalConstraint(
        name="Constraint3",
        operator=AdditionalConstraintOperator.EQUAL,
        variable=AdditionalConstraintVariable.NETTING,
        occurrences=[],
        enabled=True,
    )

    # Reads the constraint matrix
    expected_term = pd.DataFrame(np.zeros((8760, 1)))
    term = sts.get_constraint_term("constraint3")
    pd.testing.assert_frame_equal(term, expected_term)

    # Sets a new matrix
    new_term = pd.DataFrame(np.ones((8760, 1)))
    sts.set_constraint_term("constraint3", new_term)
    term = sts.get_constraint_term("constraint3")
    pd.testing.assert_frame_equal(term, new_term)


def test_error_cases(local_study_w_storage: Study) -> None:
    sts = local_study_w_storage.get_areas()["fr"].get_st_storages()["sts_1"]
    assert sts.get_constraints() == {}

    error_msg = "The short-term storage constraints only exists in v9.2+ studies"

    with pytest.raises(ValueError, match=re.escape(error_msg)):
        sts.create_constraints([STStorageAdditionalConstraint(name="Constraint1")])

    with pytest.raises(ValueError, match=re.escape(error_msg)):
        sts.update_constraint("a", STStorageAdditionalConstraintUpdate())

    with pytest.raises(ValueError, match=re.escape(error_msg)):
        sts.delete_constraints(["a"])

    with pytest.raises(ValueError, match=re.escape(error_msg)):
        sts.get_constraint_term("a")

    with pytest.raises(ValueError, match=re.escape(error_msg)):
        sts.set_constraint_term("a", pd.DataFrame())


def test_version_93(local_study_92: Study, local_study_93: Study) -> None:
    storage = local_study_93.get_areas()["fr"].create_st_storage("storage_local")
    assert storage.properties.allow_overflow is False

    # Update the overflow
    new_properties = STStoragePropertiesUpdate(allow_overflow=True)
    new_storage = storage.update_properties(new_properties)
    assert new_storage.allow_overflow is True

    # Ensures the reading also works
    study = read_study_local(Path(local_study_93.path))
    assert study.get_areas()["fr"].get_st_storages()["storage_local"].properties.allow_overflow is True

    # Ensures we cannot give nor update the overflow for a 9.2 study
    area = local_study_92.get_areas()["fr"]
    with pytest.raises(
        InvalidFieldForVersionError, match="Field allow_overflow is not a valid field for study version 9.2"
    ):
        props = STStorageProperties(allow_overflow=False)
        area.create_st_storage("new_sts", properties=props)

    sts = area.create_st_storage("new_sts")
    assert sts.properties.allow_overflow is None
    with pytest.raises(
        InvalidFieldForVersionError, match="Field allow_overflow is not a valid field for study version 9.2"
    ):
        sts.update_properties(STStoragePropertiesUpdate(allow_overflow=False))
