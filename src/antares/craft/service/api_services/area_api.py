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

from typing import Dict, List, Optional, Union

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    AreaCreationError,
    AreaDeletionError,
    AreaPropertiesUpdateError,
    AreaUiUpdateError,
    HydroCreationError,
    MatrixDownloadError,
    MatrixUploadError,
    RenewableCreationError,
    RenewableDeletionError,
    STStorageCreationError,
    STStorageDeletionError,
    ThermalCreationError,
    ThermalDeletionError,
)
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.hydro import Hydro, HydroMatrixName, HydroProperties
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage, STStorageProperties
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.api_services.utils import get_matrix, upload_series
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.tools.contents_tool import AreaUiResponse
from antares.craft.tools.matrix_tool import prepare_args_replace_matrix


class AreaApiService(BaseAreaService):
    def __init__(self, config: APIconf, study_id: str) -> None:
        super().__init__()
        self.api_config = config
        self.study_id = study_id
        self._wrapper = RequestWrapper(self.api_config.set_up_api_conf())
        self._base_url = f"{self.api_config.get_host()}/api/v1"
        self.storage_service: Optional[BaseShortTermStorageService] = None
        self.thermal_service: Optional[BaseThermalService] = None
        self.renewable_service: Optional[BaseRenewableService] = None

    def set_storage_service(self, storage_service: BaseShortTermStorageService) -> None:
        self.storage_service = storage_service

    def set_thermal_service(self, thermal_service: BaseThermalService) -> None:
        self.thermal_service = thermal_service

    def set_renewable_service(self, renewable_service: BaseRenewableService) -> None:
        self.renewable_service = renewable_service

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
                body = properties.model_dump(mode="json", exclude_none=True)
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
            area_properties = AreaProperties.model_validate(response.json())

            # TODO: Ask AntaresWeb to do the same endpoint for only one area
            url = f"{base_area_url}?type=AREA&ui=true"
            response = self._wrapper.get(url)
            json_ui = response.json()[area_id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            ui_properties = AreaUi.model_validate(ui_response.to_craft())

            hydro = self.read_hydro(area_id)

        except APIError as e:
            raise AreaCreationError(area_name, e.message) from e

        return Area(
            area_name,
            self,
            self.storage_service,
            self.thermal_service,
            self.renewable_service,
            properties=area_properties,
            ui=ui_properties,
            hydro=hydro,
        )

    def create_thermal_cluster(
        self, area_id: str, thermal_name: str, properties: Optional[ThermalClusterProperties] = None
    ) -> ThermalCluster:
        """
        Args:
            area_id: the area id of the thermal cluster
            thermal_name: the name of the thermal cluster
            properties: the properties of the thermal cluster. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created thermal cluster

        Raises:
            MissingTokenError if api_token is missing
            ThermalCreationError if an HTTP Exception occurs
        """

        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/thermal"
            body = {"name": thermal_name.lower()}
            if properties:
                camel_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response["name"]
            del json_response["name"]
            del json_response["id"]
            properties = ThermalClusterProperties.model_validate(json_response)

        except APIError as e:
            raise ThermalCreationError(thermal_name, area_id, e.message) from e

        return ThermalCluster(self.thermal_service, area_id, name, properties)

    def create_thermal_cluster_with_matrices(
        self,
        area_id: str,
        cluster_name: str,
        parameters: ThermalClusterProperties,
        prepro: Optional[pd.DataFrame] = None,
        modulation: Optional[pd.DataFrame] = None,
        series: Optional[pd.DataFrame] = None,
        CO2Cost: Optional[pd.DataFrame] = None,
        fuelCost: Optional[pd.DataFrame] = None,
    ) -> ThermalCluster:
        """
        Args:

            area_id: the area id of the thermal cluster
            cluster_name: the name of the thermal cluster
            parameters: the properties of the thermal cluster.
            prepro: prepro matrix as a pandas DataFrame.
            modulation: modulation matrix as a pandas DataFrame.
            series: matrix for series at input/thermal/series/series.txt (optional).
            CO2Cost: matrix for CO2Cost at input/thermal/series/CO2Cost.txt (optional).
            fuelCost: matrix for CO2Cost at input/thermal/series/fuelCost.txt (optional).

        Returns:
            The created thermal cluster with matrices.

        Raises:
            MissingTokenError if api_token is missing
            ThermalCreationError if an HTTP Exception occurs
        """

        try:
            url = f"{self._base_url}/studies/{self.study_id}/commands"
            body = {
                "action": "create_cluster",
                "args": {"area_id": area_id, "cluster_name": cluster_name, "parameters": {}},
            }
            args = body.get("args")

            if not isinstance(args, dict):
                raise TypeError("body['args'] must be a dictionary")

            if parameters:
                camel_properties = parameters.model_dump(mode="json", by_alias=True, exclude_none=True)
                args["parameters"].update(camel_properties)

            if prepro is not None:
                args["prepro"] = prepro.to_numpy().tolist()
            if modulation is not None:
                args["modulation"] = modulation.to_numpy().tolist()

            payload = [body]
            response = self._wrapper.post(url, json=payload)
            response.raise_for_status()

            if series is not None or CO2Cost is not None or fuelCost is not None:
                self._create_thermal_series(area_id, cluster_name, series, CO2Cost, fuelCost)

        except APIError as e:
            raise ThermalCreationError(cluster_name, area_id, e.message) from e

        return ThermalCluster(self.thermal_service, area_id, cluster_name, parameters)

    def _create_thermal_series(
        self,
        area_id: str,
        cluster_name: str,
        series: Optional[pd.DataFrame],
        CO2Cost: Optional[pd.DataFrame],
        fuelCost: Optional[pd.DataFrame],
    ) -> None:
        command_body = []
        if series is not None:
            series_path = f"input/thermal/series/{area_id}/{cluster_name.lower()}/series"
            command_body.append(prepare_args_replace_matrix(series, series_path))

        if CO2Cost is not None:
            co2_cost_path = f"input/thermal/series/{area_id}/{cluster_name.lower()}/CO2Cost"
            command_body.append(prepare_args_replace_matrix(CO2Cost, co2_cost_path))

        if fuelCost is not None:
            fuel_cost_path = f"input/thermal/series/{area_id}/{cluster_name.lower()}/fuelCost"
            command_body.append(prepare_args_replace_matrix(fuelCost, fuel_cost_path))

        if command_body:
            json_payload = command_body

            self._replace_matrix_request(json_payload)

    def _replace_matrix_request(self, json_payload: Union[Dict, List[Dict]]) -> None:
        """
        Send a POST request with the given JSON payload to commands endpoint.

        Args: Dict or List([Dict] with action = "replace_matrix" and matrix values
        """

        url = f"{self._base_url}/studies/{self.study_id}/commands"
        response = self._wrapper.post(url, json=json_payload)
        response.raise_for_status()

    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties],
        series: Optional[pd.DataFrame],
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
                camel_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response["name"]
            del json_response["name"]
            del json_response["id"]
            properties = RenewableClusterProperties.model_validate(json_response)

            if series is not None:
                series_path = f"input/renewables/series/{area_id}/{renewable_name.lower()}/series"
                command_body = [prepare_args_replace_matrix(series, series_path)]
                self._replace_matrix_request(command_body)

        except APIError as e:
            raise RenewableCreationError(renewable_name, area_id, e.message) from e

        return RenewableCluster(self.renewable_service, area_id, name, properties)

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
                camel_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**body, **camel_properties}
            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            name = json_response["name"]
            del json_response["name"]
            del json_response["id"]
            properties = STStorageProperties.model_validate(json_response)

        except APIError as e:
            raise STStorageCreationError(st_storage_name, area_id, e.message) from e

        return STStorage(self.storage_service, area_id, name, properties)

    def create_load(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/load/series/load_{area_id}"
            rows_number = series.shape[0]
            expected_rows = 8760
            if rows_number < expected_rows:
                raise MatrixUploadError(area_id, "load", f"Expected {expected_rows} rows and received {rows_number}.")
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "load", e.message) from e

    def create_wind(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/wind/series/wind_{area_id}"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "wind", e.message) from e

    def create_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/reserves/{area_id}"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "reserves", e.message) from e

    def create_solar(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/solar/series/solar_{area_id}"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "solar", e.message) from e

    def create_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        try:
            series_path = f"input/misc-gen/miscgen-{area_id}"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise MatrixUploadError(area_id, "misc-gen", e.message) from e

    def create_hydro(
        self,
        area_id: str,
        properties: Optional[HydroProperties],
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]],
    ) -> Hydro:
        # todo: not model validation because endpoint does not return anything
        #  properties = HydroProperties.model_validate(json_response) not possible

        try:
            url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/hydro/form"
            body = {}
            if properties:
                camel_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**camel_properties}
            self._wrapper.put(url, json=body)

            if matrices is not None:
                self._create_hydro_series(area_id, matrices)

        except APIError as e:
            raise HydroCreationError(area_id, e.message) from e

        return Hydro(self, area_id, properties)

    def read_hydro(
        self,
        area_id: str,
    ) -> Hydro:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/hydro/form"
        json_hydro = self._wrapper.get(url).json()

        hydro_props = HydroProperties(**json_hydro)
        hydro = Hydro(self, area_id, hydro_props)

        return hydro

    def _create_hydro_series(self, area_id: str, matrices: Dict[HydroMatrixName, pd.DataFrame]) -> None:
        command_body = []
        for matrix_name, series in matrices.items():
            if "SERIES" in matrix_name.name:
                series_path = f"input/hydro/series/{area_id}/{matrix_name.value}"
                command_body.append(prepare_args_replace_matrix(series, series_path))
            if "PREPRO" in matrix_name.name:
                series_path = f"input/hydro/prepro/{area_id}/{matrix_name.value}"
                command_body.append(prepare_args_replace_matrix(series, series_path))
            if "COMMON" in matrix_name.name:
                series_path = f"input/hydro/common/capacity/{matrix_name.value}_{area_id}"
                command_body.append(prepare_args_replace_matrix(series, series_path))
        if command_body:
            json_payload = command_body

            self._replace_matrix_request(json_payload)

    def update_area_properties(self, area_id: str, properties: AreaProperties) -> AreaProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/properties/form"
        try:
            body = properties.model_dump(mode="json", exclude_none=True)

            self._wrapper.put(url, json=body)
            response = self._wrapper.get(url)
            area_properties = AreaProperties.model_validate(response.json())

        except APIError as e:
            raise AreaPropertiesUpdateError(area_id, e.message) from e

        return area_properties

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

    def delete_area(self, area_id: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise AreaDeletionError(area_id, e.message) from e

    def delete_thermal_clusters(self, area_id: str, clusters: List[ThermalCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/thermal"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise ThermalDeletionError(area_id, body, e.message) from e

    def delete_renewable_clusters(self, area_id: str, clusters: List[RenewableCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/clusters/renewable"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise RenewableDeletionError(area_id, body, e.message) from e

    def delete_st_storages(self, area_id: str, storages: List[STStorage]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}/storages"
        body = [storage.id for storage in storages]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise STStorageDeletionError(area_id, body, e.message) from e

    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/load/series/load_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "load", e.message)

    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/solar/series/solar_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "solar", e.message)

    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/wind/series/wind_{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "wind", e.message)

    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        try:
            return get_matrix(self._base_url, self.study_id, self._wrapper, f"input/reserves/{area_id}")
        except APIError as e:
            raise MatrixDownloadError(area_id, "reserves", e.message)

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

    def read_areas(self) -> List[Area]:
        area_list = []

        base_api_url = f"{self._base_url}/studies/{self.study_id}/areas"
        ui_url = "ui=true"
        url_properties_form = "properties/form"
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
                renewables=dict_renewables,
                thermals=dict_thermals,
                st_storages=dict_st_storage,
                properties=json_properties,
                ui=ui_response,
            )

            area_list.append(area_obj)

        # sort area list to ensure reproducibility
        area_list.sort(key=lambda area: area.id)
        return area_list
