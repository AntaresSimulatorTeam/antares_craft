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
    AdequacyPatchParametersAPI,
    AdvancedAndSeedParametersAPI,
    GeneralParametersAPI,
    OptimizationParametersAPI,
    parse_thematic_trimming_api,
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
    def edit_study_settings(self, settings: StudySettingsUpdate, study_version: StudyVersion) -> None:
        try:
            edit_study_settings(self._base_url, self.study_id, self._wrapper, settings)
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
            self._wrapper.put(thematic_trimming_url, json=body)
            return get_thematic_trimming(thematic_trimming_url, self._wrapper)
        except APIError as e:
            raise ThematicTrimmingUpdateError(self.study_id, e.message) from e


def edit_study_settings(base_url: str, study_id: str, wrapper: RequestWrapper, settings: StudySettingsUpdate) -> None:
    settings_base_url = f"{base_url}/studies/{study_id}/config"

    # optimization
    if settings.optimization_parameters:
        optimization_url = f"{settings_base_url}/optimization/form"
        optimization_api_model = OptimizationParametersAPI.from_user_model(settings.optimization_parameters)
        body = optimization_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
        if "includeExportstructure" in body:
            raise APIError("AntaresWeb doesn't support editing the parameter include_exportstructure")
        wrapper.put(optimization_url, json=body)

    # general and timeseries
    if settings.general_parameters:
        general_url = f"{settings_base_url}/general/form"
        general_api_model = GeneralParametersAPI.from_user_model(settings.general_parameters)
        body = general_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
        wrapper.put(general_url, json=body)

        if nb_ts_thermal := settings.general_parameters.nb_timeseries_thermal:
            timeseries_url = f"{base_url}/studies/{study_id}/timeseries/config"
            wrapper.put(timeseries_url, json={"thermal": {"number": nb_ts_thermal}})

    # advanced and seed parameters
    if settings.advanced_parameters or settings.seed_parameters:
        advanced_parameters_url = f"{settings_base_url}/advancedparameters/form"
        advanced_api_model = AdvancedAndSeedParametersAPI.from_user_model(
            settings.advanced_parameters, settings.seed_parameters
        )
        body = advanced_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
        if "accuracyOnCorrelation" in body:
            body["accuracyOnCorrelation"] = ", ".join(corr for corr in body["accuracyOnCorrelation"])
        wrapper.put(advanced_parameters_url, json=body)

    # adequacy patch
    if settings.adequacy_patch_parameters:
        adequacy_patch_url = f"{settings_base_url}/adequacypatch/form"
        adequacy_patch_api_model = AdequacyPatchParametersAPI.from_user_model(settings.adequacy_patch_parameters)
        body = adequacy_patch_api_model.model_dump(mode="json", exclude_none=True, by_alias=True)
        wrapper.put(adequacy_patch_url, json=body)


def get_thematic_trimming(url: str, wrapper: RequestWrapper) -> ThematicTrimmingParameters:
    response = wrapper.get(url)
    return parse_thematic_trimming_api(response.json())


def read_study_settings_api(base_url: str, study_id: str, wrapper: RequestWrapper) -> StudySettings:
    settings_base_url = f"{base_url}/studies/{study_id}/config"

    # thematic trimming
    thematic_trimming_url = f"{settings_base_url}/thematictrimming/form"
    thematic_trimming_parameters = get_thematic_trimming(thematic_trimming_url, wrapper)

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
    optimization_api_model = OptimizationParametersAPI.model_validate(json_response)
    optimization_parameters = optimization_api_model.to_user_model()

    # general and timeseries
    general_url = f"{settings_base_url}/general/form"
    response = wrapper.get(general_url)
    general_api_model = GeneralParametersAPI.model_validate(response.json())
    timeseries_url = f"{base_url}/studies/{study_id}/timeseries/config"
    response = wrapper.get(timeseries_url)
    nb_ts_thermal = response.json()["thermal"]["number"]
    general_parameters = general_api_model.to_user_model(nb_ts_thermal)

    # advanced and seed parameters
    advanced_parameters_url = f"{settings_base_url}/advancedparameters/form"
    response = wrapper.get(advanced_parameters_url)
    advanced_parameters_api_model = AdvancedAndSeedParametersAPI.model_validate(response.json())
    seed_parameters = advanced_parameters_api_model.to_user_seed_parameters_model()
    advanced_parameters = advanced_parameters_api_model.to_user_advanced_parameters_model()

    # adequacy patch
    adequacy_patch_url = f"{settings_base_url}/adequacypatch/form"
    response = wrapper.get(adequacy_patch_url)
    adequacy_patch_api_model = AdequacyPatchParametersAPI.model_validate(response.json())
    adequacy_patch_parameters = adequacy_patch_api_model.to_user_model()

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=user_playlist,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )
