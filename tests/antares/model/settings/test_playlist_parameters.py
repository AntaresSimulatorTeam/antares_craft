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

from antares.craft.model.settings.playlist_parameters import PlaylistData, PlaylistParameters


class TestCreatePlaylistParameters:
    def test_create_playlist_parameters_with_list(self):
        created_params = PlaylistParameters(playlist=[PlaylistData(status=False, weight=2.1)])
        expected_model_dump = {1: {"status": False, "weight": 2.1}}
        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == expected_model_dump

    def test_create_playlist_parameters_with_dict(self):
        created_params = PlaylistParameters(
            playlist={"playlist_reset": True, "mc_years": {1: {"status": True, "weight": 3}}}
        )
        expected_model_dump = {1: {"status": True, "weight": 3}}
        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == expected_model_dump

    def test_create_playlist_with_small_dict(self, test_playlist_model_dump):
        # Given
        created_params = PlaylistParameters(playlist={1: {"status": False, "weight": 2.1}})

        # Then
        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == test_playlist_model_dump

    def test_create_playlist_parameters_with_object(self, test_playlist, test_playlist_model_dump):
        created_params = PlaylistParameters(playlist=test_playlist)

        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == test_playlist_model_dump

    def test_creating_wrong_dictionary_errors(self):
        # Given
        wrong_playlist_parameters_dict = {"playlist_reset": True, "mcyears": {1: {"status": True, "weight": 3}}}

        # Then
        with pytest.raises(ValueError, match="Not a valid playlist dictionary."):
            PlaylistParameters(playlist=wrong_playlist_parameters_dict)


class TestValidatePlaylistParameters:
    def test_playlist_parameters_validate_dict(self):
        created_params = PlaylistParameters.model_validate(
            {"playlist_reset": True, "mc_years": {1: {"status": False, "weight": 2}}}
        )
        expected_model_dump = {1: {"status": False, "weight": 2}}

        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == expected_model_dump

    def test_playlist_parameters_validate_object(self, test_playlist, test_playlist_model_dump):
        created_params = PlaylistParameters.model_validate(test_playlist)

        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == test_playlist_model_dump

    def test_validating_wrong_dictionary_gives_empty_playlist(self):
        # Given
        wrong_playlist_parameters_dict = {"playlist_reset": True, "mcyears": {1: {"status": True, "weight": 3}}}
        expected_model_dump = {}

        # When
        created_params = PlaylistParameters.model_validate(wrong_playlist_parameters_dict)

        # Then
        assert created_params
        assert isinstance(created_params, PlaylistParameters)
        assert created_params.model_dump() == expected_model_dump
