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

from typing import Any, Optional

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    LinkCreationError,
    LinkDeletionError,
    LinkDownloadError,
    LinkPropertiesUpdateError,
    LinksRetrievalError,
    LinkUiUpdateError,
    LinkUploadError,
)
from antares.craft.model.link import Link, LinkProperties, LinkUi
from antares.craft.service.api_services.utils import get_matrix, upload_series
from antares.craft.service.base_services import BaseLinkService
from typing_extensions import override


class LinkApiService(BaseLinkService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self.study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())

    @override
    def create_link(
        self,
        area_from: str,
        area_to: str,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
    ) -> Link:
        """
        Args:
            area_from: area where the link goes from
            area_to: area where the link goes to
            properties: link's properties. If not provided, AntaresWeb will use its own default values.
            ui: link's ui characteristics. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created link

        Raises:
            MissingTokenError if api_token is missing
            LinkCreationError if an HTTP Exception occurs
        """
        base_url = f"{self._base_url}/studies/{self.study_id}"
        # TODO: Currently, AntaresWeb does not have a specific endpoint for links. Once it will, we should change this logic.

        raw_url = f"{base_url}/raw?path=input/links/{area_from}/properties/{area_to}"

        try:
            url = f"{base_url}/links"
            self._wrapper.post(url, json={"area1": area_from, "area2": area_to})

            response = self._wrapper.get(raw_url)
            json_file = response.json()
            # TODO update to use check_if_none or similar
            if properties or ui:
                link_properties = (properties or LinkProperties()).model_dump(
                    mode="json", by_alias=True, exclude_none=True
                )
                link_ui = (ui or LinkUi()).model_dump(mode="json", by_alias=True, exclude_none=True)
                body = {**link_properties, **link_ui}
                if body:
                    json_file = _join_filter_values_for_json(json_file, body)
                    self._wrapper.post(raw_url, json=json_file)

            properties_keys = LinkProperties().model_dump(by_alias=True).keys()
            json_properties = {}
            for key in properties_keys:
                # TODO: This is ugly but the web structure sucks.
                value = json_file[key]
                if key in ["filter-synthesis", "filter-year-by-year"]:
                    json_properties[key] = value.split(", ") if value else value
                else:
                    json_properties[key] = value
                del json_file[key]
            ui = LinkUi.model_validate(json_file)
            created_properties = LinkProperties.model_validate(json_properties)

        except APIError as e:
            raise LinkCreationError(area_from, area_to, e.message) from e

        return Link(area_from, area_to, self, created_properties, ui)

    @override
    def delete_link(self, link: Link) -> None:
        area_from_id = link.area_from_id
        area_to_id = link.area_to_id
        url = f"{self._base_url}/studies/{self.study_id}/links/{area_from_id}/{area_to_id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise LinkDeletionError(link.id, e.message) from e

    @override
    def update_link_properties(self, link: Link, properties: LinkProperties) -> LinkProperties:
        # todo: change this code when AntaresWeb will have a real endpoint
        area1_id = link.area_from_id
        area2_id = link.area_to_id
        raw_url = f"{self._base_url}/studies/{self.study_id}/raw?path=input/links/{area1_id}/properties/{area2_id}"
        try:
            new_properties = properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not new_properties:
                return link.properties

            response = self._wrapper.get(raw_url)
            json_response = response.json()
            for key in new_properties:
                if key in ["filter-synthesis", "filter-year-by-year"]:
                    json_response[key] = ",".join(new_properties[key])
                else:
                    json_response[key] = new_properties[key]
            self._wrapper.post(raw_url, json=json_response)

            keys_to_remove = set(LinkUi().model_dump(by_alias=True).keys())
            for key in keys_to_remove:
                del json_response[key]
            for key in json_response:
                if key in ["filter-synthesis", "filter-year-by-year"]:
                    json_response[key] = json_response[key].split(", ")

            link_properties = LinkProperties.model_validate(json_response)

        except APIError as e:
            raise LinkPropertiesUpdateError(link.id, e.message) from e

        return link_properties

    @override
    def update_link_ui(self, link: Link, ui: LinkUi) -> LinkUi:
        # todo: change this code when AntaresWeb will have a real endpoint
        area1_id = link.area_from_id
        area2_id = link.area_to_id
        raw_url = f"{self._base_url}/studies/{self.study_id}/raw?path=input/links/{area1_id}/properties/{area2_id}"
        try:
            new_ui = ui.model_dump(mode="json", by_alias=True, exclude_none=True)
            if not new_ui:
                return link.ui

            response = self._wrapper.get(raw_url)
            json_response = response.json()
            json_response.update(new_ui)
            self._wrapper.post(raw_url, json=json_response)

            keys_to_remove = set(LinkProperties().model_dump(by_alias=True).keys())
            for key in keys_to_remove:
                del json_response[key]

            link_ui = LinkUi.model_validate(json_response)

        except APIError as e:
            raise LinkUiUpdateError(link.id, e.message) from e

        return link_ui

    @override
    def get_parameters(self, area_from: str, area_to: str) -> pd.DataFrame:
        try:
            parameters_path = f"input/links/{area_from}/{area_to}_parameters"
            matrix = get_matrix(self._base_url, self.study_id, self._wrapper, parameters_path)
        except APIError as e:
            raise LinkDownloadError(area_from, area_to, "parameters", e.message) from e

        return matrix

    @override
    def create_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/{area_to}_parameters"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise LinkUploadError(area_from, area_to, "parameters", e.message) from e

    @override
    def get_capacity_direct(self, area_from: str, area_to: str) -> pd.DataFrame:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_direct"
            matrix = get_matrix(self._base_url, self.study_id, self._wrapper, series_path)
        except APIError as e:
            raise LinkDownloadError(area_from, area_to, "directcapacity", e.message) from e
        return matrix

    @override
    def create_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_direct"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise LinkUploadError(area_from, area_to, "directcapacity", e.message) from e

    @override
    def get_capacity_indirect(self, area_from: str, area_to: str) -> pd.DataFrame:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_indirect"
            matrix = get_matrix(self._base_url, self.study_id, self._wrapper, series_path)
        except APIError as e:
            raise LinkDownloadError(area_from, area_to, "indirectcapacity", e.message) from e
        return matrix

    @override
    def create_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_indirect"
            upload_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise LinkUploadError(area_from, area_to, "indirectcapacity", e.message) from e

    @override
    def read_links(self) -> list[Link]:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/links"
            json_links = self._wrapper.get(url).json()
            links = []
            for link in json_links:
                link_object = self.convert_api_link_to_internal_link(link)
                links.append(link_object)

            links.sort(key=lambda link_obj: link_obj.area_from_id)
        except APIError as e:
            raise LinksRetrievalError(self.study_id, e.message) from e
        return links

    def convert_api_link_to_internal_link(self, api_link: dict[str, Any]) -> Link:
        link_area_from_id = api_link.pop("area1")
        link_area_to_id = api_link.pop("area2")

        link_style = api_link.pop("linkStyle")
        link_width = api_link.pop("linkWidth")
        color_r = api_link.pop("colorr")
        color_g = api_link.pop("colorg")
        color_b = api_link.pop("colorb")

        link_ui = LinkUi(link_style=link_style, link_width=link_width, colorr=color_r, colorg=color_g, colorb=color_b)

        mapping = {
            "hurdlesCost": "hurdles-cost",
            "loopFlow": "loop-flow",
            "usePhaseShifter": "use-phase-shifter",
            "transmissionCapacities": "transmission-capacities",
            "displayComments": "display-comments",
            "filterSynthesis": "filter-synthesis",
            "filterYearByYear": "filter-year-by-year",
            "assetType": "asset-type",
        }

        api_link = {mapping.get(k, k): v for k, v in api_link.items()}
        api_link["filter-synthesis"] = set(api_link["filter-synthesis"].split(", "))
        api_link["filter-year-by-year"] = set(api_link["filter-year-by-year"].split(", "))
        link_properties = LinkProperties(**api_link)
        return Link(link_area_from_id, link_area_to_id, self, link_properties, link_ui)


def _join_filter_values_for_json(json_dict: dict[str, Any], dict_to_extract: dict[str, Any]) -> dict[str, Any]:
    for key in dict_to_extract:
        if key in ["filter-synthesis", "filter-year-by-year"]:
            json_dict[key] = ",".join(dict_to_extract[key])
        else:
            json_dict[key] = dict_to_extract[key]
    return json_dict
