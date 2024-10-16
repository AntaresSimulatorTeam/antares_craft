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

from typing import Optional

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import (
    APIError,
    BindingConstraintDeletionError,
    StudyDeletionError,
    StudySettingsUpdateError,
)
from antares.model.binding_constraint import BindingConstraint
from antares.model.settings import (
    AdequacyPatchProperties,
    AdvancedProperties,
    GeneralProperties,
    OptimizationProperties,
    StudySettings,
    ThematicTrimming,
    TimeSeriesProperties,
)
from antares.service.base_services import BaseStudyService


def _returns_study_settings(
    base_url: str, study_id: str, wrapper: RequestWrapper, update: bool, settings: Optional[StudySettings]
) -> Optional[StudySettings]:
    settings_base_url = f"{base_url}/studies/{study_id}/config"
    mapping = {
        "general_properties": ("general", GeneralProperties),
        "thematic_trimming": ("thematictrimming", ThematicTrimming),
        "time_series_properties": ("timeseries", TimeSeriesProperties),
        "adequacy_patch_properties": ("adequacypatch", AdequacyPatchProperties),
        "advanced_properties": ("advancedparameters", AdvancedProperties),
        "optimization_properties": ("optimization", OptimizationProperties),
        "playlist": ("playlist", None),
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
        if settings_type == "playlist":
            settings_property = response.json()
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

    @property
    def study_id(self) -> str:
        return self._study_id

    @property
    def config(self) -> APIconf:
        return self._config

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
