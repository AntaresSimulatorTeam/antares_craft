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
