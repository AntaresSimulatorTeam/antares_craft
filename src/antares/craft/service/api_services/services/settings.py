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
from dataclasses import asdict

from typing_extensions import override

from antares.craft import ThematicTrimmingParameters
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    StudySettingsReadError,
    StudySettingsUpdateError,
    ThematicTrimmingUpdateError,
)
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.study_settings import StudySettings, StudySettingsUpdate
from antares.craft.service.api_services.models.settings import (
    OptimizationParametersAPI,
    parse_adequacy_patch_parameters_api,
    parse_advanced_and_seed_parameters_api,
    parse_general_parameters_api,
    parse_optimization_parameters_api,
    parse_thematic_trimming_api,
    serialize_adequacy_patch_parameters_api,
    serialize_advanced_and_seed_parameters_api,
    serialize_general_parameters_api,
    serialize_thematic_trimming_api,
)
from antares.craft.service.base_services import BaseStudySettingsService
from antares.study.version import StudyVersion


class StudySettingsAPIService(BaseStudySettingsService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def edit_study_settings(
        self, settings: StudySettingsUpdate, current_settings: StudySettings, study_version: StudyVersion
    ) -> StudySettings:
        try:
            return edit_study_settings(self._base_url, self.study_id, self._wrapper, settings, current_settings)
        except APIError as e:
            raise StudySettingsUpdateError(self.study_id, e.message) from e

    @override
    def read_study_settings(self) -> StudySettings:
        try:
            return read_study_settings_api(self._base_url, self.study_id, self._wrapper)
        except APIError as e:
            raise StudySettingsReadError(self.study_id, e.message) from e

    @override
    def set_playlist(self, new_playlist: dict[int, PlaylistParameters]) -> None:
        playlist_url = f"{self._base_url}/studies/{self.study_id}/config/playlist/form"
        body = {}
        for key, value in new_playlist.items():
            body[str(key)] = asdict(value)
        self._wrapper.put(playlist_url, json=body)

    @override
    def set_thematic_trimming(self, new_thematic_trimming: ThematicTrimmingParameters) -> ThematicTrimmingParameters:
        try:
            thematic_trimming_url = f"{self._base_url}/studies/{self.study_id}/config/thematictrimming/form"
            body = serialize_thematic_trimming_api(new_thematic_trimming)
            response = self._wrapper.put(thematic_trimming_url, json=body)
            return parse_thematic_trimming_api(response.json())
        except APIError as e:
            raise ThematicTrimmingUpdateError(self.study_id, e.message) from e


def edit_study_settings(
    base_url: str,
    study_id: str,
    wrapper: RequestWrapper,
    settings: StudySettingsUpdate,
    current_settings: StudySettings,
) -> StudySettings:
    settings_base_url = f"{base_url}/studies/{study_id}/config"

    # optimization
    optimization_parameters = None
    if settings.optimization_parameters:
        optimization_url = f"{settings_base_url}/optimization/form"
        optimization_api_model = OptimizationParametersAPI.from_user_model(settings.optimization_parameters)
        body = optimization_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
        if "includeExportstructure" in body:
            raise APIError("AntaresWeb doesn't support editing the parameter include_exportstructure")
        json_response = wrapper.put(optimization_url, json=body).json()
        optimization_parameters = parse_optimization_parameters_api(json_response)

    # general and timeseries
    general_parameters = None
    if settings.general_parameters:
        # Timeseries
        timeseries_url = f"{base_url}/studies/{study_id}/timeseries/config"
        if nb_ts_thermal := settings.general_parameters.nb_timeseries_thermal:
            response = wrapper.put(timeseries_url, json={"thermal": {"number": nb_ts_thermal}}).json()
        else:
            response = wrapper.get(timeseries_url).json()
        nb_ts_thermal = response["thermal"]["number"]
        assert isinstance(nb_ts_thermal, int)

        # General
        general_url = f"{settings_base_url}/general/form"
        body = serialize_general_parameters_api(settings.general_parameters)
        response = wrapper.put(general_url, json=body).json()
        general_parameters = parse_general_parameters_api(response, nb_ts_thermal)

    # advanced and seed parameters
    advanced_parameters, seed_parameters = None, None
    if settings.advanced_parameters or settings.seed_parameters:
        advanced_parameters_url = f"{settings_base_url}/advancedparameters/form"
        body = serialize_advanced_and_seed_parameters_api(settings.advanced_parameters, settings.seed_parameters)
        response = wrapper.put(advanced_parameters_url, json=body)
        advanced_parameters, seed_parameters = parse_advanced_and_seed_parameters_api(response.json())

    # adequacy patch
    adequacy_patch_parameters = None
    if settings.adequacy_patch_parameters:
        adequacy_patch_url = f"{settings_base_url}/adequacypatch/form"
        body = serialize_adequacy_patch_parameters_api(settings.adequacy_patch_parameters)
        response = wrapper.put(adequacy_patch_url, json=body).json()
        adequacy_patch_parameters = parse_adequacy_patch_parameters_api(response)

    return StudySettings(
        general_parameters=general_parameters or current_settings.general_parameters,
        optimization_parameters=optimization_parameters or current_settings.optimization_parameters,
        seed_parameters=seed_parameters or current_settings.seed_parameters,
        advanced_parameters=advanced_parameters or current_settings.advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters or current_settings.adequacy_patch_parameters,
        playlist_parameters=current_settings.playlist_parameters,
        thematic_trimming_parameters=current_settings.thematic_trimming_parameters,
    )


def read_study_settings_api(base_url: str, study_id: str, wrapper: RequestWrapper) -> StudySettings:
    settings_base_url = f"{base_url}/studies/{study_id}/config"

    # thematic trimming
    thematic_trimming_url = f"{settings_base_url}/thematictrimming/form"
    response = wrapper.get(thematic_trimming_url)
    thematic_trimming_parameters = parse_thematic_trimming_api(response.json())

    # playlist
    playlist_url = f"{settings_base_url}/playlist/form"
    response = wrapper.get(playlist_url)
    json_response = response.json()
    user_playlist = {}
    for key, value in json_response.items():
        user_playlist[int(key)] = PlaylistParameters(**value)

    # optimization
    optimization_url = f"{settings_base_url}/optimization/form"
    response = wrapper.get(optimization_url)
    json_response = response.json()
    optimization_parameters = parse_optimization_parameters_api(json_response)

    # general and timeseries
    timeseries_url = f"{base_url}/studies/{study_id}/timeseries/config"
    response = wrapper.get(timeseries_url)
    nb_ts_thermal = response.json()["thermal"]["number"]

    general_url = f"{settings_base_url}/general/form"
    response = wrapper.get(general_url).json()
    general_parameters = parse_general_parameters_api(response, nb_ts_thermal)

    # advanced and seed parameters
    advanced_parameters_url = f"{settings_base_url}/advancedparameters/form"
    response = wrapper.get(advanced_parameters_url)
    advanced_parameters, seed_parameters = parse_advanced_and_seed_parameters_api(response.json())

    # adequacy patch
    adequacy_patch_url = f"{settings_base_url}/adequacypatch/form"
    response = wrapper.get(adequacy_patch_url).json()
    adequacy_patch_parameters = parse_adequacy_patch_parameters_api(response)

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=user_playlist,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )
