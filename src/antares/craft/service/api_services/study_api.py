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
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Optional

import antares.craft.model.study as study

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    BindingConstraintDeletionError,
    OutputDeletionError,
    OutputsRetrievalError,
    StudyDeletionError,
    StudyMoveError,
    StudySettingsReadError,
    StudySettingsUpdateError,
    StudyVariantCreationError,
    TaskFailedError,
    TaskTimeOutError,
    ThermalTimeseriesGenerationError,
)
from antares.craft.model.binding_constraint import BindingConstraint
from antares.craft.model.output import Output
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.service.api_services.study_settings_api import (
    AdequacyPatchParametersAPI,
    AdvancedAndSeedParametersAPI,
    GeneralParametersAPI,
    OptimizationParametersAPI,
    ThematicTrimmingParametersAPI,
)
from antares.craft.service.api_services.utils import wait_task_completion
from antares.craft.service.base_services import BaseOutputService, BaseStudyService

if TYPE_CHECKING:
    from antares.craft.model.study import Study


def _edit_study_settings(base_url: str, study_id: str, wrapper: RequestWrapper, settings: StudySettings) -> None:
    settings_base_url = f"{base_url}/studies/{study_id}/config"

    # thematic trimming
    if settings.thematic_trimming_parameters:
        thematic_trimming_url = f"{settings_base_url}/thematictrimming/form"
        api_model = ThematicTrimmingParametersAPI.from_user_model(settings.thematic_trimming_parameters)
        body = api_model.model_dump(mode="json", exclude_unset=True, by_alias=True)
        wrapper.put(thematic_trimming_url, json=body)

    # playlist
    if settings.playlist_parameters:
        playlist_url = f"{settings_base_url}/playlist/form"
        body = {}
        for key, value in settings.playlist_parameters.items():
            body[str(key)] = asdict(value)
        wrapper.put(playlist_url, json=body)

    # optimization
    if settings.optimization_parameters:
        optimization_url = f"{settings_base_url}/optimization/form"
        optimization_api_model = OptimizationParametersAPI.from_user_model(settings.optimization_parameters)
        body = optimization_api_model.model_dump(mode="json", exclude_unset=True, by_alias=True)
        wrapper.put(optimization_url, json=body)

    # general and timeseries
    if settings.general_parameters:
        general_url = f"{settings_base_url}/general/form"
        general_api_model = GeneralParametersAPI.from_user_model(settings.general_parameters)
        body = general_api_model.model_dump(mode="json", exclude_unset=True, by_alias=True)
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
        body = advanced_api_model.model_dump(mode="json", exclude_unset=True, by_alias=True)
        wrapper.put(advanced_parameters_url, json=body)

    # adequacy patch
    if settings.adequacy_patch_parameters:
        adequacy_patch_url = f"{settings_base_url}/adequacypatch/form"
        adequacy_patch_api_model = AdequacyPatchParametersAPI.from_user_model(settings.adequacy_patch_parameters)
        body = adequacy_patch_api_model.model_dump(mode="json", exclude_unset=True, by_alias=True)
        wrapper.put(adequacy_patch_url, json=body)


def read_study_settings(base_url: str, study_id: str, wrapper: RequestWrapper) -> StudySettings:
    settings_base_url = f"{base_url}/studies/{study_id}/config"
    try:
        # thematic trimming
        thematic_trimming_url = f"{settings_base_url}/thematictrimming/form"
        response = wrapper.get(thematic_trimming_url)
        thematic_trimming_api_model = ThematicTrimmingParametersAPI.model_validate(response.json())
        thematic_trimming_parameters = thematic_trimming_api_model.to_user_model()

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
        optimization_api_model = OptimizationParametersAPI.model_validate(response.json())
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

    except APIError as e:
        raise StudySettingsReadError(study_id, e.message) from e

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=user_playlist,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )


class StudyApiService(BaseStudyService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self._config = config
        self._study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())
        self._output_service: Optional[BaseOutputService] = None

    @property
    def study_id(self) -> str:
        return self._study_id

    @property
    def config(self) -> APIconf:
        return self._config

    @property
    def output_service(self) -> Optional[BaseOutputService]:
        return self._output_service

    def set_output_service(self, output_service: BaseOutputService) -> None:
        self._output_service = output_service

    def update_study_settings(self, settings: StudySettings) -> None:
        try:
            _edit_study_settings(self._base_url, self.study_id, self._wrapper, settings)
        except APIError as e:
            raise StudySettingsUpdateError(self.study_id, e.message) from e

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint.id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise BindingConstraintDeletionError(constraint.id, e.message) from e

    def delete(self, children: bool) -> None:
        url = f"{self._base_url}/studies/{self.study_id}?children={children}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise StudyDeletionError(self.study_id, e.message) from e

    def create_variant(self, variant_name: str) -> "Study":
        url = f"{self._base_url}/studies/{self.study_id}/variants?name={variant_name}"
        try:
            response = self._wrapper.post(url)
            variant_id = response.json()
            return study.read_study_api(self.config, variant_id)
        except APIError as e:
            raise StudyVariantCreationError(self.study_id, e.message) from e

    def read_outputs(self) -> list[Output]:
        url = f"{self._base_url}/studies/{self.study_id}/outputs"
        try:
            response = self._wrapper.get(url)
            outputs_json_list = response.json()
            return [
                Output(output_service=self.output_service, name=output["name"], archived=output["archived"])
                for output in outputs_json_list
            ]
        except APIError as e:
            raise OutputsRetrievalError(self.study_id, e.message)

    def delete_outputs(self) -> None:
        outputs_url = f"{self._base_url}/studies/{self.study_id}/outputs"
        try:
            response = self._wrapper.get(outputs_url)
            outputs_json_list = response.json()
            if not outputs_json_list:
                raise OutputsRetrievalError(self.study_id, "No outputs to delete.")
            for output in outputs_json_list:
                output_name = output["name"]
                self.delete_output(output_name)
        except APIError as e:
            raise OutputsRetrievalError(self.study_id, e.message)

    def delete_output(self, output_name: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/outputs/{output_name}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise OutputDeletionError(self.study_id, output_name, e.message) from e

    def move_study(self, new_parent_path: Path) -> PurePath:
        url = f"{self._base_url}/studies/{self.study_id}/move?folder_dest={new_parent_path}"
        try:
            self._wrapper.put(url)
            json_study = self._wrapper.get(f"{self._base_url}/studies/{self.study_id}").json()
            folder = json_study.pop("folder")
            return PurePath(folder) if folder else PurePath(".")
        except APIError as e:
            raise StudyMoveError(self.study_id, new_parent_path.as_posix(), e.message) from e

    def generate_thermal_timeseries(self) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/timeseries/generate"
        try:
            response = self._wrapper.put(url)
            task_id = response.json()
            wait_task_completion(self._base_url, self._wrapper, task_id)
        except (APIError, TaskFailedError, TaskTimeOutError) as e:
            raise ThermalTimeseriesGenerationError(self.study_id, e.message)
