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
    AdvancedParametersUpdate,
    ExportMPS,
    GeneralParametersUpdate,
    HydroPricingMode,
    OptimizationTransmissionCapacities,
    PlaylistParameters,
    StudySettingsUpdate,
    ThematicTrimmingParameters,
    UnitCommitmentMode,
    create_study_local,
    read_study_local,
)
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter


def test_update_settings(tmp_path: Path) -> None:
    # test update study settings
    settings = StudySettingsUpdate()
    settings.general_parameters = GeneralParametersUpdate(nb_years=4)
    settings.advanced_parameters = AdvancedParametersUpdate(unit_commitment_mode=UnitCommitmentMode.MILP)
    study = create_study_local("second_study", "880", tmp_path)
    study.update_settings(settings)
    assert study.get_settings().general_parameters.nb_years == 4
    assert study.get_settings().advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP
    # 2nd update
    settings = StudySettingsUpdate()
    settings.general_parameters = GeneralParametersUpdate(nb_years=2)
    settings.advanced_parameters = AdvancedParametersUpdate(hydro_pricing_mode=HydroPricingMode.ACCURATE)
    study.update_settings(settings)
    assert study.get_settings().general_parameters.nb_years == 2
    assert study.get_settings().advanced_parameters.hydro_pricing_mode == HydroPricingMode.ACCURATE
    assert study.get_settings().advanced_parameters.unit_commitment_mode == UnitCommitmentMode.MILP


def test_playlist(tmp_path: Path) -> None:
    study = create_study_local("second_study", "880", tmp_path)
    settings = study.get_settings()
    assert settings.playlist_parameters == {}
    # Create 3 years
    new_settings = StudySettingsUpdate(general_parameters=GeneralParametersUpdate(nb_years=3))
    study.update_settings(new_settings)
    # Checks the `set` method
    new_playlist = {
        1: PlaylistParameters(status=True, weight=4.0),
        2: PlaylistParameters(status=True, weight=1),
        3: PlaylistParameters(status=False, weight=1),
    }
    study.set_playlist(new_playlist)
    assert study.get_settings().playlist_parameters == new_playlist
    # Checks the `reading` method
    study_path = Path(study.path)
    study = read_study_local(study_path)
    playlist = study.get_settings().playlist_parameters
    assert playlist == new_playlist
    # Checks the ini content
    ini_path = study_path / "settings" / "generaldata.ini"
    content = ini_path.read_text()
    assert (
        """[playlist]
playlist_reset = True
playlist_year - = 2
playlist_year_weight = 0,4.0"""
        in content
    )

    # Updates playlist again
    new_playlist = {
        1: PlaylistParameters(status=True, weight=2.5),
        2: PlaylistParameters(status=False),
        3: PlaylistParameters(status=False),
    }
    study.set_playlist(new_playlist)
    assert study.get_settings().playlist_parameters == new_playlist
    # Checks the `reading` method
    study = read_study_local(study_path)
    playlist = study.get_settings().playlist_parameters
    assert playlist == new_playlist
    # Checks the ini content
    content = ini_path.read_text()
    assert (
        """[playlist]
playlist_reset = False
playlist_year + = 0
playlist_year_weight = 0,2.5"""
        in content
    )


def test_thematic_trimming_methods(tmp_path: Path) -> None:
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


def test_thematic_trimming(tmp_path: Path) -> None:
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


def test_wrongly_formatted_fields_that_we_do_not_care_about(tmp_path: Path) -> None:
    study = create_study_local("second_study", "880", tmp_path)
    study_path = Path(study.path)
    ini_path = study_path / "settings" / "generaldata.ini"
    with open(ini_path, "r") as ini_file:
        new_lines = ini_file.readlines()
        for k, line in enumerate(new_lines):
            if "intra-modal" in line:
                new_lines[k] = "intra-modal = load, wind, solar\n"
    with open(ini_path, "w") as ini_file:
        ini_file.writelines(new_lines)
    # Asserts the reading succeeds even thought the fields has a value we do not expect
    read_study_local(study_path)


def test_export_mps(tmp_path: Path) -> None:
    study = create_study_local("second_study", "880", tmp_path)
    study_path = Path(study.path)
    ini_path = study_path / "settings" / "generaldata.ini"
    with open(ini_path, "r") as ini_file:
        new_lines = ini_file.readlines()
        for k, line in enumerate(new_lines):
            if "include-exportmps" in line:
                new_lines[k] = "include-exportmps = None\n"
    with open(ini_path, "w") as ini_file:
        ini_file.writelines(new_lines)
    # Asserts the reading succeeds with an unusual exportMps value
    study = read_study_local(study_path)
    assert study.get_settings().optimization_parameters.include_exportmps == ExportMPS.FALSE


@pytest.mark.parametrize("value", ["", "wind", "wind, load"])
def test_accuracy_on_correlation(tmp_path: Path, value: str) -> None:
    """Asserts the reading succeeds with different accuracy_on_correlation values"""
    study = create_study_local("second_study", "880", tmp_path)
    study_path = Path(study.path)
    ini_path = study_path / "settings" / "generaldata.ini"
    with open(ini_path, "r") as ini_file:
        new_lines = ini_file.readlines()
        for k, line in enumerate(new_lines):
            if "accuracy-on-correlation" in line:
                new_lines[k] = f"accuracy-on-correlation = {value}\n"
    with open(ini_path, "w") as ini_file:
        ini_file.writelines(new_lines)
    read_study_local(study_path)


@pytest.mark.parametrize("value", [True, False, "infinite"])
def test_transmission_capacities(tmp_path: Path, value: bool | str) -> None:
    study = create_study_local("study", "880", tmp_path)
    study_path = Path(study.path)
    ini_path = study_path / "settings" / "generaldata.ini"
    ini_content = IniReader().read(ini_path)
    ini_content["optimization"]["transmission-capacities"] = value
    IniWriter().write(ini_content, ini_path)
    # Ensure we're able to read the study
    study = read_study_local(study_path)
    transmission_value = study.get_settings().optimization_parameters.transmission_capacities
    # Ensure we converted the legacy value into the right new one
    if value is True:
        assert transmission_value == OptimizationTransmissionCapacities.LOCAL_VALUES
    elif value == "infinite":
        assert transmission_value == OptimizationTransmissionCapacities.INFINITE_FOR_ALL_LINKS
    else:
        assert transmission_value == OptimizationTransmissionCapacities.NULL_FOR_ALL_LINKS
