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
import json
from typing import Optional, List, Dict

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import (
    APIError,
    BindingConstraintDeletionError,
    StudyDeletionError,
    StudySettingsUpdateError,
)
from antares.model.area import Area, AreaProperties
from antares.model.binding_constraint import BindingConstraint
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.model.settings.adequacy_patch import AdequacyPatchParameters
from antares.model.settings.advanced_parameters import AdvancedParameters
from antares.model.settings.general import GeneralParameters
from antares.model.settings.optimization import OptimizationParameters
from antares.model.settings.playlist_parameters import PlaylistData, PlaylistParameters
from antares.model.settings.study_settings import StudySettings
from antares.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.model.settings.time_series import TimeSeriesParameters
from antares.model.st_storage import STStorage, STStorageProperties
from antares.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.service.base_services import BaseStudyService


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

    def read_areas(self) -> List:
        area_list = []

        base_api_url = f"{self._base_url}/studies/{self.study_id}/areas"
        ui_url = "?ui=true"
        url_thermal = f"clusters/thermal"
        url_renewable = f"clusters/renewable"
        url_st_storage = "storages"
        url_properties_form = f"properties/form"

        json_resp = self._wrapper.get(base_api_url + ui_url).json()

        for area in json_resp:
            thermals = dict()
            renewables = dict()
            st_storage = dict()

            area_url = base_api_url + "/" + f"{area}/"
            json_thermal = self._wrapper.get(area_url + url_thermal).json()
            json_renewable = self._wrapper.get(area_url + url_renewable).json()
            json_st_storage = self._wrapper.get(area_url + url_st_storage).json()
            json_properties = self._wrapper.get(area_url + url_properties_form).json()

            for therm in json_thermal:
                id_therm = therm.pop('id')
                name = therm.pop('name')

                thermal_props=ThermalClusterProperties(**therm)
                therm_cluster=ThermalCluster(self.config, area, name, thermal_props)
                thermals.update({id_therm: therm_cluster})

            for renew in json_renewable:
                id_renew = renew.pop('id')
                name = renew.pop('name')

                renew_props=RenewableClusterProperties(**renew)
                renew_cluster=RenewableCluster(self.config, area, name, renew_props)
                renewables.update({id_renew: renew_cluster})

            for storage in json_st_storage:
                id_storage = storage.pop('id')
                name = storage.pop('name')

                storage_props = STStorageProperties(**storage)
                st_storage_cl = STStorage(self.config, area, name, storage_props)
                st_storage.update({id_storage:st_storage_cl})

            area_obj=Area(area,
                    self.config, self.config,
                    self.config, self.config,
                    renewables=renewables,thermals=thermals,
                    st_storages=st_storage, properties=json_properties)

            area_list.append(area_obj)

        return area_list