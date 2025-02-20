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

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    HydroPropertiesReadingError,
    HydroPropertiesUpdateError,
    MatrixDownloadError,
    MatrixUploadError,
)
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate
from antares.craft.service.api_services.models.hydro import HydroPropertiesAPI
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import BaseHydroService
from typing_extensions import override


class HydroApiService(BaseHydroService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"

    @override
    def read_properties(self, area_id: str) -> HydroProperties:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/hydro/form"
            json_hydro = self._wrapper.get(url).json()

            hydro_props = HydroPropertiesAPI(**json_hydro).to_user_model()
        except APIError as e:
            raise HydroPropertiesReadingError(area_id, e.message) from e

        return hydro_props

    @override
    def update_properties(self, area_id: str, properties: HydroPropertiesUpdate) -> None:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/hydro/form"
            api_model = HydroPropertiesAPI.from_user_model(properties)
            body = {**api_model.model_dump(mode="json", by_alias=True, exclude_none=True)}
            self._wrapper.put(url, json=body)
        except APIError as e:
            raise HydroPropertiesUpdateError(area_id, e.message) from e

    @override
    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/maxpower_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "maxpower", e.message) from e

    @override
    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/reservoir_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "reservoir", e.message) from e

    @override
    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/inflowPattern_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "inflow_pattern", e.message) from e

    @override
    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/creditmodulations_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "credit_modulations", e.message) from e

    @override
    def get_water_values(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(
                self._base_url, self.study_id, self._wrapper, f"input/hydro/common/capacity/waterValues_{area_id}"
            )
        except APIError as e:
            raise MatrixDownloadError(area_id, "water_values", e.message) from e

    @override
    def get_ror_series(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/hydro/series/{area_id}/ror")
        except APIError as e:
            raise MatrixDownloadError(area_id, "ror", e.message) from e

    @override
    def get_mod_series(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/hydro/series/{area_id}/mod")
        except APIError as e:
            raise MatrixDownloadError(area_id, "mod", e.message) from e

    @override
    def get_mingen(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/hydro/series/{area_id}/mingen")
        except APIError as e:
            raise MatrixDownloadError(area_id, "mingen", e.message) from e

    @override
    def get_energy(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/hydro/prepro/{area_id}/energy")
        except APIError as e:
            raise MatrixDownloadError(area_id, "energy", e.message) from e

    @override
    def update_maxpower(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url, self.study_id, self._wrapper, series, f"input/hydro/common/capacity/maxpower_{area_id}"
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "max_power", e.message) from e

    @override
    def update_reservoir(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url, self.study_id, self._wrapper, series, f"input/hydro/common/capacity/reservoir_{area_id}"
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "reservoir", e.message) from e

    @override
    def update_inflow_pattern(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/common/capacity/inflowPattern_{area_id}",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "inflow_pattern", e.message) from e

    @override
    def update_credits_modulation(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/common/capacity/creditmodulations_{area_id}",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "credit_modulations", e.message) from e

    @override
    def update_water_values(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/common/capacity/waterValues_{area_id}",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "water_values", e.message) from e

    @override
    def update_ror_series(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(self._base_url, self.study_id, self._wrapper, series, f"input/hydro/series/{area_id}/ror")
        except APIError as e:
            raise MatrixUploadError(area_id, "ror", e.message) from e

    @override
    def update_mod_series(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/series/{area_id}/mod",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "mod", e.message) from e

    @override
    def update_mingen(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/series/{area_id}/mingen",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "mingen", e.message) from e

    @override
    def update_energy(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            update_series(
                self._base_url,
                self.study_id,
                self._wrapper,
                series,
                f"input/hydro/prepro/{area_id}/energy",
            )
        except APIError as e:
            raise MatrixUploadError(area_id, "energy", e.message) from e
