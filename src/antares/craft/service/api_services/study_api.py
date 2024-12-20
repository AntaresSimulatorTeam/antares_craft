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
from typing import TYPE_CHECKING, Optional

import antares.craft.model.study as study

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    BindingConstraintDeletionError,
    OutputsRetrievalError,
    StudyDeletionError,
    StudySettingsUpdateError,
    StudyVariantCreationError,
)
from antares.craft.model.binding_constraint import BindingConstraint
from antares.craft.model.output import Output
from antares.craft.model.settings.adequacy_patch import AdequacyPatchParameters
from antares.craft.model.settings.advanced_parameters import AdvancedParameters
from antares.craft.model.settings.general import GeneralParameters
from antares.craft.model.settings.optimization import OptimizationParameters
from antares.craft.model.settings.playlist_parameters import PlaylistData, PlaylistParameters
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.craft.model.settings.time_series import TimeSeriesParameters
from antares.craft.service.base_services import BaseOutputService, BaseStudyService

if TYPE_CHECKING:
    from antares.craft.model.study import Study


def _returns_study_settings(
    base_url: str, study_id: str, wrapper: RequestWrapper, update: bool, settings: Optional[StudySettings]
) -> Optional[StudySettings]:
    settings_base_url = f"{base_url}/studies/{study_id}/config"
    mapping = {
        "general_parameters": ("general", GeneralParameters),
        "thematic_trimming_parameters": ("thematictrimming", ThematicTrimmingParameters),
        "time_series_parameters": ("timeseries", TimeSeriesParameters),
        "adequacy_patch_parameters": ("adequacypatch", AdequacyPatchParameters),
        "advanced_parameters": ("advancedparameters", AdvancedParameters),
        "optimization_parameters": ("optimization", OptimizationParameters),
        "playlist_parameters": ("playlist", PlaylistParameters),
    }
    if settings:
        json_settings = settings.model_dump(mode="json", by_alias=True, exclude_none=True)
        if not json_settings and update:
            return None

        for key, value in json_settings.items():
            url = f"{settings_base_url}/{mapping[key][0]}/form"
            wrapper.put(url, json=value)

    json_settings = {}
    for settings_type, settings_tuple in mapping.items():
        settings_class = settings_tuple[1]
        url = f"{settings_base_url}/{settings_tuple[0]}/form"
        response = wrapper.get(url)
        if settings_type == "playlist_parameters":
            mc_years = [PlaylistData.model_validate(year) for year in response.json().values()]
            settings_property = settings_class(playlist=mc_years) if mc_years else None
        else:
            settings_property = settings_class.model_validate(response.json())  # type: ignore
        json_settings[settings_type] = settings_property

    return StudySettings.model_validate(json_settings)


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

    def update_study_settings(self, settings: StudySettings) -> Optional[StudySettings]:
        try:
            new_settings = _returns_study_settings(self._base_url, self.study_id, self._wrapper, True, settings)
        except APIError as e:
            raise StudySettingsUpdateError(self.study_id, e.message) from e
        return new_settings

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
