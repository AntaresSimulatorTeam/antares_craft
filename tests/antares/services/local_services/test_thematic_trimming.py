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

from dataclasses import asdict, replace
from pathlib import Path

from antares.craft import (
    ThematicTrimmingParameters,
    create_study_local,
    read_study_local,
)
from antares.craft.exceptions.exceptions import InvalidFieldForVersionError

DEFAULT_THEMATIC_TRIMMING_PARAMETERS_88 = ThematicTrimmingParameters(
    psp_open_injection=True,
    psp_open_withdrawal=True,
    psp_open_level=True,
    psp_closed_injection=True,
    psp_closed_withdrawal=True,
    psp_closed_level=True,
    pondage_injection=True,
    pondage_withdrawal=True,
    pondage_level=True,
    battery_injection=True,
    battery_withdrawal=True,
    battery_level=True,
    other1_injection=True,
    other1_withdrawal=True,
    other1_level=True,
    other2_injection=True,
    other2_withdrawal=True,
    other2_level=True,
    other3_injection=True,
    other3_withdrawal=True,
    other3_level=True,
    other4_injection=True,
    other4_withdrawal=True,
    other4_level=True,
    other5_injection=True,
    other5_withdrawal=True,
    other5_level=True,
)


def test_class_methods(tmp_path: Path) -> None:
    none_fields = {
        "psp_open_injection",
        "psp_open_withdrawal",
        "psp_open_level",
        "psp_closed_injection",
        "psp_closed_withdrawal",
        "psp_closed_level",
        "pondage_injection",
        "pondage_withdrawal",
        "pondage_level",
        "battery_injection",
        "battery_withdrawal",
        "battery_level",
        "other1_injection",
        "other1_withdrawal",
        "other1_level",
        "other2_injection",
        "other2_withdrawal",
        "other2_level",
        "other3_injection",
        "other3_withdrawal",
        "other3_level",
        "other4_injection",
        "other4_withdrawal",
        "other4_level",
        "other5_injection",
        "other5_withdrawal",
        "other5_level",
        "sts_by_group",
    }

    trimming = ThematicTrimmingParameters(spil_enrg=False)
    args = asdict(trimming)
    for key, value in args.items():
        if key == "spil_enrg":
            assert value is False
        elif key in none_fields:
            assert value is None
        else:
            assert value is True

    # Reverse it
    new_trimming = trimming.all_reversed()
    args = asdict(new_trimming)
    for key, value in args.items():
        if key == "spil_enrg":
            assert value is True
        elif key in none_fields:
            assert value is None
        else:
            assert value is False

    # Enable everything
    all_true_trimming = trimming.all_enabled()
    assert all_true_trimming == ThematicTrimmingParameters()
    # Disable everything
    all_false_trimming = trimming.all_disabled()
    args = asdict(all_false_trimming)
    for key, value in args.items():
        if key in none_fields:
            assert value is None
        else:
            assert value is False


def test_nominal_case(tmp_path: Path) -> None:
    study = create_study_local("second_study", "880", tmp_path)
    settings = study.get_settings()
    assert settings.thematic_trimming_parameters == DEFAULT_THEMATIC_TRIMMING_PARAMETERS_88
    # Checks the `set` method
    new_trimming = ThematicTrimmingParameters(sts_cashflow_by_cluster=False, nuclear=False)
    study.set_thematic_trimming(new_trimming)
    expected_trimming = replace(DEFAULT_THEMATIC_TRIMMING_PARAMETERS_88, sts_cashflow_by_cluster=False, nuclear=False)
    assert study.get_settings().thematic_trimming_parameters == expected_trimming
    # Checks the `reading` method
    study_path = Path(study.path)
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == expected_trimming
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
    expected_trimming = expected_trimming.all_reversed()
    assert study.get_settings().thematic_trimming_parameters == expected_trimming
    # Checks the `reading` method
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == expected_trimming
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


def test_error_cases(tmp_path: Path) -> None:
    study = create_study_local("second_study", "8.8", tmp_path)
    # Asserts we can't set `sts_by_group` as it's a 9.2 field
    for value in [True, False]:
        new_trimming = ThematicTrimmingParameters(sts_by_group=value)
        with pytest.raises(
            InvalidFieldForVersionError, match="Field sts_by_group is not a valid field for study version 8.8"
        ):
            study.set_thematic_trimming(new_trimming)

    # Asserts we can't set `psp_open_level` as the field disappeared in version 9.2
    study = create_study_local("study", "9.2", tmp_path)
    for value in [True, False]:
        new_trimming = ThematicTrimmingParameters(psp_open_level=value)
        with pytest.raises(
            InvalidFieldForVersionError, match="Field psp_open_level is not a valid field for study version 9.2"
        ):
            study.set_thematic_trimming(new_trimming)


def test_92(tmp_path: Path) -> None:
    study = create_study_local("second_study", "9.2", tmp_path)
    for study_9_2 in [study, read_study_local(tmp_path / "second_study")]:
        settings = study_9_2.get_settings()
        # Ensures `sts_by_group` is not None as we have a 9.2 study
        assert settings.thematic_trimming_parameters == ThematicTrimmingParameters(sts_by_group=True)
    # Checks the `set` method
    new_trimming = ThematicTrimmingParameters(ov_cost=False, nuclear=False)
    study.set_thematic_trimming(new_trimming)
    # We expect the sts_by_group field to be set as we have a 9.2 study
    expected_trimming = ThematicTrimmingParameters(ov_cost=False, nuclear=False, sts_by_group=True)
    assert study.get_settings().thematic_trimming_parameters == expected_trimming
    # Checks the `reading` method
    study_path = Path(study.path)
    study = read_study_local(study_path)
    trimming = study.get_settings().thematic_trimming_parameters
    assert trimming == expected_trimming
