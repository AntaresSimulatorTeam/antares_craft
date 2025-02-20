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

from typing import Any, Optional, Union

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    AreaCreationError,
    AreaDeletionError,
    AreaPropertiesUpdateError,
    AreasRetrievalError,
    AreaUiUpdateError,
    MatrixDownloadError,
    MatrixUploadError,
    RenewableCreationError,
    RenewableDeletionError,
    STStorageCreationError,
    STStorageDeletionError,
    ThermalCreationError,
    ThermalDeletionError,
)
from antares.craft.model.area import Area, AreaProperties, AreaPropertiesUpdate, AreaUi
from antares.craft.model.hydro import Hydro
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage, STStorageProperties
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.api_services.models.area import AreaPropertiesAPI
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.models.st_storage import STStoragePropertiesAPI
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseHydroService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.tools.contents_tool import AreaUiResponse
from antares.craft.tools.matrix_tool import prepare_args_replace_matrix
from typing_extensions import override


class AreaApiService(BaseAreaService):
    def __init__(
        self,
        config: APIconf,
        study_id: str,
        storage_service: BaseShortTermStorageService,
        thermal_service: BaseThermalService,
        renewable_service: BaseRenewableService,
        hydro_service: BaseHydroService,
    ) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"
        self.storage_service: BaseShortTermStorageService = storage_service
        self.thermal_service: BaseThermalService = thermal_service
        self.renewable_service: BaseRenewableService = renewable_service
        self.hydro_service: BaseHydroService = hydro_service

    @override
    def create_area(
        self, area_name: str, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        """
        Args:
            area_name: area's name to be created.
            properties: area's properties. If not provided, AntaresWeb will use its own default values.
            ui: area's ui characteristics. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created area

        Raises:
            MissingTokenError if api_token is missing
            AreaCreationError if an HTTP Exception occurs
        """
        # todo: AntaresWeb is stupid and x, y and color_rgb fields are mandatory ...
        base_area_url = f"{self._base_url}/studies/{self.study_id}/areas"

        try:
            response = self._wrapper.post(base_area_url, json={"name": area_name, "type": "AREA"})
            area_id = response.json()["id"]

            if properties:
                url = f"{base_area_url}/{area_id}/properties/form"
                api_model = AreaPropertiesAPI.from_user_model(properties)
                # todo: change this exclude when AntaresWeb will work
                exclude = {"spread_unsupplied_energy_cost", "spread_spilled_energy_cost"}
                body = api_model.model_dump(mode="json", by_alias=True, exclude_none=True, exclude=exclude)
                if body:
                    self._wrapper.put(url, json=body)
            if ui:
                json_content = ui.model_dump(exclude_none=True)
                url = f"{base_area_url}/{area_id}/ui"
                if "layer" in json_content:
                    layer = json_content["layer"]
                    url += f"?layer={layer}"
                    del json_content["layer"]
                if json_content:
                    # Gets current UI
                    response = self._wrapper.get(f"{base_area_url}?type=AREA&ui=true")
                    json_ui = response.json()[area_id]
                    ui_response = AreaUiResponse.model_validate(json_ui)
                    current_ui = ui_response.to_craft()
                    del current_ui["layer"]
                    # Updates the UI
                    current_ui.update(json_content)
                    self._wrapper.put(url, json=current_ui)

            url = f"{base_area_url}/{area_id}/properties/form"
            response = self._wrapper.get(url)
            api_properties = AreaPropertiesAPI.model_validate(response.json())
            area_properties = api_properties.to_user_model()

            # TODO: Ask AntaresWeb to do the same endpoint for only one area
            url = f"{base_area_url}?type=AREA&ui=true"
            response = self._wrapper.get(url)
            json_ui = response.json()[area_id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            ui_properties = AreaUi.model_validate(ui_response.to_craft())

            hydro_properties = self.hydro_service.read_properties(area_id)
            hydro = Hydro(self.hydro_service, area_id, hydro_properties)

        except APIError as e:
            raise AreaCreationError(area_name, e.message) from e

        return Area(
            area_name,
            self,
            self.storage_service,
            self.thermal_service,
            self.renewable_service,
            self.hydro_service,
            properties=area_properties,
            ui=ui_properties,
            hydro=hydro,
        )

    @override
    def create_thermal_cluster(
        self,
        area_id: str,
        cluster_name: str,
        properties: Optional[ThermalClusterProperties] = None,
        prepro: Optional[pd.DataFrame] = None,
        modulation: Optional[pd.DataFrame] = None,
        series: Optional[pd.DataFrame] = None,
        co2_cost: Optional[pd.DataFrame] = None,
        fuel_cost: Optional[pd.DataFrame] = None,
    ) -> ThermalCluster:
        """
        Args:

            area_id: the area id of the thermal cluster
            cluster_name: the name of the thermal cluster
            properties: the properties of the thermal cluster.
            prepro: prepro matrix as a pandas DataFrame.
            modulation: modulation matrix as a pandas DataFrame.
            series: matrix for series at input/thermal/series/series.txt (optional).
            co2_cost: matrix for CO2Cost at input/thermal/series/CO2Cost.txt (optional).
            fuel_cost: matrix for CO2Cost at input/thermal/series/fuelCost.txt (optional).

        Returns:
            The created thermal cluster with matrices.

        Raises:
            MissingTokenError if api_token is missing
            ThermalCreationError if an HTTP Exception occurs
        """
        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/thermal"
            body = {"name": cluster_name.lower()}
            if properties:
                api_properties = ThermalClusterPropertiesAPI.from_user_model(properties)
                camel_properties = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response.pop("name")
            thermal_id = json_response.pop("id")
            created_api_properties = ThermalClusterPropertiesAPI.model_validate(json_response)
            properties = created_api_properties.to_user_model()

            # Upload matrices
            if prepro is not None:
                matrix_path = f"input/thermal/prepro/{area_id}/{thermal_id}/data"
                update_series(self._base_url, self.study_id, self._wrapper, prepro, matrix_path)
            if modulation is not None:
                matrix_path = f"input/thermal/prepro/{area_id}/{thermal_id}/modulation"
                update_series(self._base_url, self.study_id, self._wrapper, modulation, matrix_path)
            if series is not None:
                matrix_path = f"input/thermal/series/{area_id}/{thermal_id}/series"
                update_series(self._base_url, self.study_id, self._wrapper, series, matrix_path)
            if co2_cost is not None:
                matrix_path = f"input/thermal/series/{area_id}/{thermal_id}/CO2Cost"
                update_series(self._base_url, self.study_id, self._wrapper, co2_cost, matrix_path)
            if fuel_cost is not None:
                matrix_path = f"input/thermal/series/{area_id}/{thermal_id}/fuelCost"
                update_series(self._base_url, self.study_id, self._wrapper, fuel_cost, matrix_path)

        except APIError as e:
            raise ThermalCreationError(cluster_name, area_id, e.message) from e

        return ThermalCluster(self.thermal_service, area_id, name, properties)

    def _replace_matrix_request(self, json_payload: Union[dict[str, Any], list[dict[str, Any]]]) -> None:
        """
        Send a POST request with the given JSON payload to commands endpoint.

        Args: dict or list([dict] with action = "replace_matrix" and matrix values
        """

        url = f"{self._base_url}/studies/{self.study_id}/commands"
        response = self._wrapper.post(url, json=json_payload)
        response.raise_for_status()

    @override
    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties] = None,
        series: Optional[pd.DataFrame] = None,
    ) -> RenewableCluster:
        """
        Args:
            area_id: the area id of the renewable cluster
            renewable_name: the name of the renewable cluster
            properties: the properties of the renewable cluster. If not provided, AntaresWeb will use its own default values
            series: matrix for series.txt

        Returns:
            The created renewable cluster

        Raises:
            MissingTokenError if api_token is missing
            RenewableCreationError if an HTTP Exception occurs
        """
        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/renewable"
            body = {"name": renewable_name.lower()}
            if properties:
                api_model = RenewableClusterPropertiesAPI.from_user_model(properties)
                camel_properties = api_model.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response.pop("name")
            del json_response["id"]
            api_properties = RenewableClusterPropertiesAPI.model_validate(json_response)
            properties = api_properties.to_user_model()

            if series is not None:
                series_path = f"input/renewables/series/{area_id}/{renewable_name.lower()}/series"
                command_body = [prepare_args_replace_matrix(series, series_path)]
                self._replace_matrix_request(command_body)

        except APIError as e:
            raise RenewableCreationError(renewable_name, area_id, e.message) from e

        return RenewableCluster(self.renewable_service, area_id, name, properties)

    @override
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        """
        Args:
            area_id: the area id of the short term storage
            st_storage_name: the name of the short term storage
            properties: the properties of the short term storage. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created renewable cluster

        Raises:
            MissingTokenError if api_token is missing
            STStorageCreationError if an HTTP Exception occurs
        """
        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages"
            body = {"name": st_storage_name}
            if properties:
                api_model = STStoragePropertiesAPI.from_user_model(properties)
                camel_properties = api_model.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response.pop("name")
            del json_response["id"]
            api_properties = STStoragePropertiesAPI.model_validate(json_response)
            properties = api_properties.to_user_model()

        except APIError as e:
            raise STStorageCreationError(st_storage_name, area_id, e.message) from e

        return STStorage(self.storage_service, area_id, name, properties)

    @override
    def create_load(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/load/series/load_{area_id}"
            rows_number = series.shape[0]
            expected_rows = 8760
            if rows_number < expected_rows:
                raise MatrixUploadError(area_id, "load", f"Expected {expected_rows} rows and received {rows_number}.")
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "load", e.message) from e

    @override
    def create_wind(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/wind/series/wind_{area_id}"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "wind", e.message) from e

    @override
    def create_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/reserves/{area_id}"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "reserves", e.message) from e

    @override
    def create_solar(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/solar/series/solar_{area_id}"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "solar", e.message) from e

    @override
    def create_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/misc-gen/miscgen-{area_id}"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "misc-gen", e.message) from e

    @override
    def update_area_properties(self, area_id: str, properties: AreaPropertiesUpdate) -> AreaProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/properties/form"
        try:
            api_model = AreaPropertiesAPI.from_user_model(properties)
            # todo: change this exclude when AntaresWeb will work
            exclude = {"spread_unsupplied_energy_cost", "spread_spilled_energy_cost"}
            body = api_model.model_dump(mode="json", by_alias=True, exclude_none=True, exclude=exclude)

            self._wrapper.put(url, json=body)
            response = self._wrapper.get(url)
            api_properties = AreaPropertiesAPI.model_validate(response.json())
            area_properties = api_properties.to_user_model()

        except APIError as e:
            raise AreaPropertiesUpdateError(area_id, e.message) from e

        return area_properties

    @override
    def update_area_ui(self, area_id: str, ui: AreaUi) -> AreaUi:
        base_url = f"{self._base_url}/studies/{self.study_id}/areas"
        try:
            url = f"{base_url}/{area_id}/ui"
            json_content = ui.model_dump(exclude_none=True)
            if "layer" in json_content:
                layer = json_content["layer"]
                url += f"?layer={layer}"
                del json_content["layer"]

            # Gets current UI
            response = self._wrapper.get(f"{base_url}?type=AREA&ui=true")
            json_ui = response.json()[area_id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            current_ui = ui_response.to_craft()
            del current_ui["layer"]
            # Updates the UI
            current_ui.update(json_content)
            self._wrapper.put(url, json=current_ui)

            url = f"{base_url}?type=AREA&ui=true"
            response = self._wrapper.get(url)
            json_ui = response.json()[area_id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            area_ui = AreaUi.model_validate(ui_response.to_craft())

        except APIError as e:
            raise AreaUiUpdateError(area_id, e.message) from e

        return area_ui

    @override
    def delete_area(self, area_id: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise AreaDeletionError(area_id, e.message) from e

    @override
    def delete_thermal_clusters(self, area_id: str, clusters: list[ThermalCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/thermal"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise ThermalDeletionError(area_id, body, e.message) from e

    @override
    def delete_renewable_clusters(self, area_id: str, clusters: list[RenewableCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/renewable"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise RenewableDeletionError(area_id, body, e.message) from e

    @override
    def delete_st_storages(self, area_id: str, storages: list[STStorage]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages"
        body = [storage.id for storage in storages]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise STStorageDeletionError(area_id, body, e.message) from e

    @override
    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/load/series/load_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "load", e.message)

    @override
    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/solar/series/solar_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "solar", e.message)

    @override
    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/wind/series/wind_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "wind", e.message)

    @override
    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/reserves/{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "reserves", e.message)

    @override
    def get_misc_gen_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/misc-gen/miscgen-{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "misc-gen", e.message)

    def craft_ui(self, url_str: str, area_id: str) -> AreaUi:
        response = self._wrapper.get(url_str)
        json_ui = response.json()[area_id]

        ui_response = AreaUiResponse.model_validate(json_ui)
        current_ui = AreaUi.model_validate(ui_response.to_craft())

        return current_ui

    @override
    def read_areas(self) -> list[Area]:
        area_list = []

        base_api_url = f"{self._base_url}/studies/{self.study_id}/areas"
        ui_url = "ui=true"
        url_properties_form = "properties/form"
        try:
            json_resp = self._wrapper.get(base_api_url + "?" + ui_url).json()
            for area in json_resp:
                area_url = base_api_url + "/" + f"{area}/"

                json_properties = self._wrapper.get(area_url + url_properties_form).json()

                ui_response = self.craft_ui(f"{base_api_url}?type=AREA&{ui_url}", area)

                assert self.renewable_service is not None
                assert self.thermal_service is not None
                assert self.storage_service is not None

                renewables = self.renewable_service.read_renewables(area)
                thermals = self.thermal_service.read_thermal_clusters(area)
                st_storages = self.storage_service.read_st_storages(area)

                dict_renewables = {renewable.id: renewable for renewable in renewables}

                dict_thermals = {thermal.id: thermal for thermal in thermals}
                dict_st_storage = {storage.id: storage for storage in st_storages}

                area_obj = Area(
                    area,
                    self,
                    self.storage_service,
                    self.thermal_service,
                    self.renewable_service,
                    self.hydro_service,
                    renewables=dict_renewables,
                    thermals=dict_thermals,
                    st_storages=dict_st_storage,
                    properties=json_properties,
                    ui=ui_response,
                )
                area_obj.hydro.read_properties()

                area_list.append(area_obj)

            # sort area list to ensure reproducibility
            area_list.sort(key=lambda area: area.id)

        except APIError as e:
            raise AreasRetrievalError(self.study_id, e.message) from e

        return area_list
