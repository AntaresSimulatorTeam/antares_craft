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

from dataclasses import asdict
from pathlib import Path

from antares.craft import (
    ThematicTrimmingParameters,
    create_study_local,
    read_study_local,
)
from antares.craft.exceptions.exceptions import InvalidFieldForVersionError


def test_class_methods(tmp_path: Path) -> None:
    trimming = ThematicTrimmingParameters(spil_enrg=False)
    args = asdict(trimming)
    assert args.pop("spil_enrg") is False
    assert args.pop("sts_by_group") is None
    for field in args:
        assert args[field] is True

    # Reverse it
    new_trimming = trimming.all_reversed()
    args = asdict(new_trimming)
    assert args.pop("spil_enrg") is True
    assert args.pop("sts_by_group") is None
    for field in args:
        assert args[field] is False

    # Enable everything
    all_true_trimming = trimming.all_enabled()
    assert all_true_trimming == ThematicTrimmingParameters()
    # Disable everything
    all_false_trimming = trimming.all_disabled()
    args = asdict(all_false_trimming)
    assert args.pop("sts_by_group") is None
    for field in args:
        assert args[field] is False


def test_nominal_case(tmp_path: Path) -> None:
    study = create_study_local("second_study", "880", tmp_path)
    settings = study.get_settings()
    assert settings.thematic_trimming_parameters == ThematicTrimmingParameters()
    # Checks the `set` method
    new_trimming = ThematicTrimmingParameters(sts_cashflow_by_cluster=False, nuclear=False)
    study.set_thematic_trimming(new_trimming)
    assert study.get_settings().thematic_trimming_parameters == new_trimming
    # Checks the `reading` method
    study_path = Path(study.path)
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == new_trimming
    # Checks the ini content
    ini_path = study_path / "settings" / "generaldata.ini"
    content = ini_path.read_text()
    assert (
        """[variables selection]
selected_vars_reset = True
select_var - = NUCLEAR
select_var - = STS Cashflow By Cluster
"""
        in content
    )

    # Inverts the trimming
    new_trimming = new_trimming.all_reversed()
    study.set_thematic_trimming(new_trimming)
    assert study.get_settings().thematic_trimming_parameters == new_trimming
    # Checks the `reading` method
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == new_trimming
    # Checks the ini content
    content = ini_path.read_text()
    assert (
        """[variables selection]
selected_vars_reset = False
select_var + = NUCLEAR
select_var + = STS Cashflow By Cluster"""
        in content
    )

    # Disable everything
    all_disabled_trimming = new_trimming.all_disabled()
    study.set_thematic_trimming(all_disabled_trimming)
    content = ini_path.read_text()
    assert (
        """[variables selection]
selected_vars_reset = False"""
        in content
    )


def test_88(tmp_path: Path) -> None:
    study = create_study_local("second_study", "8.8", tmp_path)
    # Asserts we can't set `sts_by_group` as it's a 9.2 field
    for value in [True, False]:
        new_trimming = ThematicTrimmingParameters(sts_by_group=value)
        with pytest.raises(
            InvalidFieldForVersionError, match="Field sts_by_group is not a valid field for study version 8.8"
        ):
            study.set_thematic_trimming(new_trimming)


def test_92(tmp_path: Path) -> None:
    study = create_study_local("second_study", "9.2", tmp_path)
    settings = study.get_settings()
    assert settings.thematic_trimming_parameters == ThematicTrimmingParameters()
    # Checks the `set` method
    new_trimming = ThematicTrimmingParameters(sts_cashflow_by_cluster=False, nuclear=False)
    study.set_thematic_trimming(new_trimming)
    # We expect the sts_by_group field to be set as we have a 9.2 study
    expected_trimming = ThematicTrimmingParameters(sts_cashflow_by_cluster=False, nuclear=False, sts_by_group=True)
    assert study.get_settings().thematic_trimming_parameters == expected_trimming
    # Checks the `reading` method
    study_path = Path(study.path)
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == expected_trimming
