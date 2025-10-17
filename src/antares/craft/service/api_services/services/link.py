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

from typing import Dict, Optional

import pandas as pd

from typing_extensions import override

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    LinkCreationError,
    LinkDeletionError,
    LinkDownloadError,
    LinksPropertiesUpdateError,
    LinksRetrievalError,
    LinkUiUpdateError,
    LinkUploadError,
)
from antares.craft.model.link import Link, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
from antares.craft.service.api_services.models.link import LinkPropertiesAndUiAPI
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import BaseLinkService


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
        try:
            url = f"{self._base_url}/studies/{self.study_id}/links"
            body = {"area1": area_from, "area2": area_to}

            if properties or ui:
                api_model = LinkPropertiesAndUiAPI.from_user_model(ui, properties)
                body.update(api_model.model_dump(mode="json", by_alias=True, exclude_none=True))

            response = self._wrapper.post(url, json=body)
            json_response = response.json()
            area_from = json_response.pop("area1")
            area_to = json_response.pop("area2")
            api_response = LinkPropertiesAndUiAPI.model_validate(json_response)
            link_properties = api_response.to_properties_user_model()
            link_ui = api_response.to_ui_user_model()

        except APIError as e:
            raise LinkCreationError(area_from, area_to, e.message) from e

        return Link(area_from, area_to, self, link_properties, link_ui)

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
    def update_link_ui(self, link: Link, ui: LinkUiUpdate) -> LinkUi:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/links/{link.area_from_id}/{link.area_to_id}"
            api_ui = LinkPropertiesAndUiAPI.from_user_model(ui, None)
            body = api_ui.model_dump(mode="json", by_alias=True, exclude_none=True)

            response = self._wrapper.put(url, json=body)
            json_response = response.json()

            json_response.pop("area1")
            json_response.pop("area2")
            api_response = LinkPropertiesAndUiAPI.model_validate(json_response)
            link_ui = api_response.to_ui_user_model()

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
    def set_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/{area_to}_parameters"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
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
    def set_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_direct"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
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
    def set_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        try:
            series_path = f"input/links/{area_from}/capacities/{area_to}_indirect"
            update_series(self._base_url, self.study_id, self._wrapper, series, series_path)
        except APIError as e:
            raise LinkUploadError(area_from, area_to, "indirectcapacity", e.message) from e

    @override
    def read_links(self) -> dict[str, Link]:
        try:
            url = f"{self._base_url}/studies/{self.study_id}/links"
            json_links = self._wrapper.get(url).json()
            links = {}
            for link in json_links:
                area_from = link.pop("area1")
                area_to = link.pop("area2")
                api_response = LinkPropertiesAndUiAPI.model_validate(link)
                link_properties = api_response.to_properties_user_model()
                link_ui = api_response.to_ui_user_model()
                link = Link(area_from, area_to, self, link_properties, link_ui)
                links[link.id] = link

        except APIError as e:
            raise LinksRetrievalError(self.study_id, e.message) from e
        return links

    @override
    def update_links_properties(self, new_properties: Dict[str, LinkPropertiesUpdate]) -> Dict[str, LinkProperties]:
        body = {}
        for link_id, props in new_properties.items():
            api_properties = LinkPropertiesAndUiAPI.from_user_model(None, props)
            api_dict = api_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
            body[link_id] = api_dict

        try:
            url = f"{self._base_url}/studies/{self.study_id}/table-mode/links"
            links = self._wrapper.put(url, json=body).json()
            updated_links: Dict[str, LinkProperties] = {}

            for link in links:
                links[link].pop("area1")
                links[link].pop("area2")
                api_response = LinkPropertiesAndUiAPI.model_validate(links[link])
                link_properties = api_response.to_properties_user_model()

                updated_links[link] = link_properties

        except APIError as e:
            raise LinksPropertiesUpdateError(self.study_id, e.message) from e

        return updated_links
