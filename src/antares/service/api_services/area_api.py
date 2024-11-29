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

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.exceptions.exceptions import (
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
from antares.model.area import Area, AreaProperties, AreaUi
from antares.model.hydro import Hydro, HydroMatrixName, HydroProperties
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.model.st_storage import STStorage, STStorageProperties
from antares.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.service.base_services import (
    BaseAreaService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.tools.contents_tool import AreaUiResponse
from antares.tools.matrix_tool import prepare_args_replace_matrix


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

    def _upload_series(self, area: Area, series: pd.DataFrame, path: str, matrix_type: str) -> None:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/raw?path={path}"
            array_data = series.to_numpy().tolist()
            self._wrapper.post(url, json=array_data)
        except APIError as e:
            raise MatrixUploadError(area.id, matrix_type, e.message) from e

    def create_load(self, area: Area, series: pd.DataFrame) -> None:
        series_path = f"input/load/series/load_{area.id}"
        rows_number = series.shape[0]
        expected_rows = 8760
        if rows_number < expected_rows:
            raise MatrixUploadError(area.id, "load", f"Expected {expected_rows} rows and received {rows_number}.")
        self._upload_series(area, series, series_path, "load")

    def create_wind(self, area: Area, series: pd.DataFrame) -> None:
        series_path = f"input/wind/series/wind_{area.id}"
        self._upload_series(area, series, series_path, "wind")

    def create_reserves(self, area: Area, series: pd.DataFrame) -> None:
        series_path = f"input/reserves/{area.id}"
        self._upload_series(area, series, series_path, "reserves")

    def create_solar(self, area: Area, series: pd.DataFrame) -> None:
        series_path = f"input/solar/series/solar_{area.id}"
        self._upload_series(area, series, series_path, "solar")

    def create_misc_gen(self, area: Area, series: pd.DataFrame) -> None:
        series_path = f"input/misc-gen/miscgen-{area.id}"
        self._upload_series(area, series, series_path, "misc-gen")

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

    def update_area_properties(self, area: Area, properties: AreaProperties) -> AreaProperties:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area.id}/properties/form"
        try:
            body = properties.model_dump(mode="json", exclude_none=True)
            if not body:
                return area.properties

            self._wrapper.put(url, json=body)
            response = self._wrapper.get(url)
            area_properties = AreaProperties.model_validate(response.json())

        except APIError as e:
            raise AreaPropertiesUpdateError(area.id, e.message) from e

        return area_properties

    def update_area_ui(self, area: Area, ui: AreaUi) -> AreaUi:
        base_url = f"{self._base_url}/studies/{self.study_id}/areas"
        try:
            url = f"{base_url}/{area.id}/ui"
            json_content = ui.model_dump(exclude_none=True)
            if "layer" in json_content:
                layer = json_content["layer"]
                url += f"?layer={layer}"
                del json_content["layer"]
            if not json_content:
                return area.ui

            # Gets current UI
            response = self._wrapper.get(f"{base_url}?type=AREA&ui=true")
            json_ui = response.json()[area.id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            current_ui = ui_response.to_craft()
            del current_ui["layer"]
            # Updates the UI
            current_ui.update(json_content)
            self._wrapper.put(url, json=current_ui)

            url = f"{base_url}?type=AREA&ui=true"
            response = self._wrapper.get(url)
            json_ui = response.json()[area.id]
            ui_response = AreaUiResponse.model_validate(json_ui)
            area_ui = AreaUi.model_validate(ui_response.to_craft())

        except APIError as e:
            raise AreaUiUpdateError(area.id, e.message) from e

        return area_ui

    def delete_area(self, area: Area) -> None:
        area_id = area.id
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise AreaDeletionError(area_id, e.message) from e

    def delete_thermal_clusters(self, area: Area, clusters: List[ThermalCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area.id}/clusters/thermal"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise ThermalDeletionError(area.id, body, e.message) from e

    def delete_renewable_clusters(self, area: Area, clusters: List[RenewableCluster]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area.id}/clusters/renewable"
        body = [cluster.id for cluster in clusters]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise RenewableDeletionError(area.id, body, e.message) from e

    def delete_st_storages(self, area: Area, storages: List[STStorage]) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/areas/{area.id}/storages"
        body = [storage.id for storage in storages]
        try:
            self._wrapper.delete(url, json=body)
        except APIError as e:
            raise STStorageDeletionError(area.id, body, e.message) from e

    def get_matrix(self, area_id: str, series_path: str, matrix_type: str) -> pd.DataFrame:
        try:
            raw_url = f"{self._base_url}/studies/{self.study_id}/raw?path={series_path}"
            response = self._wrapper.get(raw_url)
            json_df = response.json()
            dataframe = pd.DataFrame(data=json_df["data"], index=json_df["index"], columns=json_df["columns"])
            return dataframe
        except APIError as e:
            raise MatrixDownloadError(area_id, matrix_type, e.message) from e

    def get_load_matrix(self, area: Area) -> pd.DataFrame:
        return self.get_matrix(area.id, f"input/load/series/load_{area.id}", "load")

    def get_solar_matrix(self, area: Area) -> pd.DataFrame:
        return self.get_matrix(area.id, f"input/solar/series/solar_{area.id}", "solar")

    def get_wind_matrix(self, area: Area) -> pd.DataFrame:
        return self.get_matrix(area.id, f"input/wind/series/wind_{area.id}", "wind")

    def get_reserves_matrix(self, area: Area) -> pd.DataFrame:
        return self.get_matrix(area.id, f"input/reserves/{area.id}", "reserves")

    def get_misc_gen_matrix(self, area: Area) -> pd.DataFrame:
        return self.get_matrix(area.id, f"input/misc-gen/miscgen-{area.id}", "misc-gen")

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
