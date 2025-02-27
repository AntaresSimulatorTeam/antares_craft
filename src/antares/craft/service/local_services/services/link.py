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

import os

from configparser import DuplicateSectionError
from typing import Any, Dict, Optional

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import LinkCreationError
from antares.craft.model.link import Link, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
from antares.craft.service.base_services import BaseLinkService
from antares.craft.service.local_services.models.link import LinkPropertiesAndUiLocal
from antares.craft.tools.contents_tool import sort_ini_sections
from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class LinkLocalService(BaseLinkService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

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
            properties: link's properties
            ui: link's ui characteristics
            existing_areas: existing areas from study

        Returns:
            The created link

        Raises:
            LinkCreationError if an area doesn't exist or existing areas have not been provided
        """

        link_dir = self.config.study_path / "input/links" / area_from
        os.makedirs(link_dir, exist_ok=True)
        local_model = LinkPropertiesAndUiLocal.from_user_model(ui or LinkUi(), properties or LinkProperties())

        properties_ini_file = link_dir / "properties.ini"
        properties_ini = CustomRawConfigParser()

        if properties_ini_file.is_file():
            with open(properties_ini_file, "r") as ini_file:
                properties_ini.read_file(ini_file)
        try:
            properties_ini.add_section(area_to)
        except DuplicateSectionError:
            raise LinkCreationError(
                area_from=area_from,
                area_to=area_to,
                message=f"Link exists already between '{area_from}' and '{area_to}'.",
            )
        ini_dict = local_model.model_dump(mode="json", by_alias=True)
        properties_ini[area_to] = self.sort_link_properties_dict(ini_dict)

        properties_ini = sort_ini_sections(properties_ini)

        with open(properties_ini_file, "w") as ini_file:
            properties_ini.write(ini_file)

        return Link(
            area_from=area_from,
            area_to=area_to,
            link_service=self,
            properties=local_model.to_properties_user_model(),  # round-trip for pydantic validation
            ui=local_model.to_ui_user_model(),
        )

    @override
    def delete_link(self, link: Link) -> None:
        raise NotImplementedError

    @override
    def update_link_properties(self, link: Link, properties: LinkPropertiesUpdate) -> LinkProperties:
        raise NotImplementedError

    @override
    def update_link_ui(self, link: Link, ui: LinkUiUpdate) -> LinkUi:
        raise NotImplementedError

    # TODO maybe put sorting functions together
    @staticmethod
    def sort_link_properties_dict(ini_dict: Dict[str, str]) -> Dict[str, str]:
        dict_order = [
            "hurdles-cost",
            "loop-flow",
            "use-phase-shifter",
            "transmission-capacities",
            "asset-type",
            "link-style",
            "link-width",
            "colorr",
            "colorg",
            "colorb",
            "display-comments",
            "filter-synthesis",
            "filter-year-by-year",
            "comments",
        ]
        return dict(sorted(ini_dict.items(), key=lambda item: dict_order.index(item[0])))

    @override
    def create_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

    @override
    def create_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

    @override
    def create_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

    @override
    def get_capacity_direct(
        self,
        area_from: str,
        area_to: str,
    ) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.LINKS_CAPACITIES_DIRECT,
            self.config.study_path,
            area_id=area_from,
            second_area_id=area_to,
        )

    @override
    def get_capacity_indirect(
        self,
        area_from: str,
        area_to: str,
    ) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT,
            self.config.study_path,
            area_id=area_from,
            second_area_id=area_to,
        )

    @override
    def get_parameters(
        self,
        area_from: str,
        area_to: str,
    ) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.LINKS_PARAMETERS, self.config.study_path, area_id=area_from, second_area_id=area_to
        )

    @override
    def read_links(self) -> list[Link]:
        link_path = self.config.study_path / "input" / "links"

        link_clusters = []

        for element in link_path.iterdir():
            area_from = element.name
            links_dict = IniFile(
                self.config.study_path, InitializationFilesTypes.LINK_PROPERTIES_INI, area_id=area_from
            ).ini_dict
            # If the properties.ini doesn't exist, we stop the reading process
            if links_dict:
                for area_to, values in links_dict.items():
                    local_model = LinkPropertiesAndUiLocal.model_validate(values)
                    properties = local_model.to_properties_user_model()
                    ui = local_model.to_ui_user_model()
                    link_clusters.append(
                        Link(
                            area_from=area_from,
                            area_to=area_to,
                            link_service=self,
                            properties=properties,
                            ui=ui,
                        )
                    )
        return link_clusters

    @override
    def update_multiple_links(self, dict_links: Dict[str, LinkPropertiesUpdate]) -> Dict[str, LinkProperties]:
        raise NotImplementedError
