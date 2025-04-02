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

from antares.craft import (
    AdvancedParametersUpdate,
    GeneralParametersUpdate,
    HydroPricingMode,
    PlaylistParameters,
    StudySettingsUpdate,
    UnitCommitmentMode,
    create_study_local,
    read_study_local,
)
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


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
    # Write a playlist into the file
    study_path = Path(study.path)
    ini_path = study_path / "settings" / "generaldata.ini"
    ini_content = IniReader(DUPLICATE_KEYS).read(ini_path)
    ini_content["playlist"] = {"playlist_reset": False, "playlist_year +": [0, 1], "playlist_year_weight": ["0,4.0"]}
    IniWriter(DUPLICATE_KEYS).write(ini_content, ini_path)
    # Checks the value read
    study = read_study_local(study_path)
    playlist = study.get_settings().playlist_parameters
    assert playlist == {
        0: PlaylistParameters(status=True, weight=4.0),
        1: PlaylistParameters(status=True, weight=1),
        2: PlaylistParameters(status=False, weight=1),
    }
