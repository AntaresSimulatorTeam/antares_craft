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
from antares.craft.model.link import Link, LinkProperties, LinkPropertiesLocal, LinkUi, LinkUiLocal
from antares.craft.service.base_services import BaseLinkService
from antares.craft.tools.contents_tool import sort_ini_sections
from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class LinkLocalService(BaseLinkService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

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
        local_properties = (
            LinkPropertiesLocal.model_validate(properties.model_dump(mode="json", exclude_none=True))
            if properties
            else LinkPropertiesLocal()
        )
        local_ui = LinkUiLocal.model_validate(ui.model_dump(mode="json", exclude_none=True)) if ui else LinkUiLocal()

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
        ini_dict = dict(local_properties.ini_fields)
        ini_dict.update(local_ui.ini_fields)
        properties_ini[area_to] = self.sort_link_properties_dict(ini_dict)

        properties_ini = sort_ini_sections(properties_ini)

        with open(properties_ini_file, "w") as ini_file:
            properties_ini.write(ini_file)

        return Link(
            area_from=area_from,
            area_to=area_to,
            link_service=self,
            properties=local_properties.yield_link_properties(),
            ui=local_ui.yield_link_ui(),
        )

    def delete_link(self, link: Link) -> None:
        raise NotImplementedError

    def update_link_properties(self, link: Link, properties: LinkProperties) -> LinkProperties:
        raise NotImplementedError

    def update_link_ui(self, link: Link, ui: LinkUi) -> LinkUi:
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
        ]
        return dict(sorted(ini_dict.items(), key=lambda item: dict_order.index(item[0])))

    def create_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

    def create_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

    def create_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        raise NotImplementedError

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

    def get_parameters(
        self,
        area_from: str,
        area_to: str,
    ) -> pd.DataFrame:
        return read_timeseries(
            TimeSeriesFileType.LINKS_PARAMETERS, self.config.study_path, area_id=area_from, second_area_id=area_to
        )

    def read_links(self) -> list[Link]:
        link_path = self.config.study_path / "input" / "links"

        link_clusters = []

        for element in link_path.iterdir():
            area_from = element.name
            links_dict = IniFile(self.config.study_path, IniFileTypes.LINK_PROPERTIES_INI, area_id=area_from).ini_dict
            # If the properties.ini doesn't exist, we stop the reading process
            if links_dict:
                for area_to in links_dict:
                    # Extract and delete from original dictionnary, the ui related properties
                    ui_fields = ["link-style", "link-width", "colorr", "colorg", "colorb"]
                    properties_field = {
                        field: links_dict[area_to].pop(field) for field in ui_fields if field in links_dict[area_to]
                    }

                    ui_properties = LinkUiLocal.model_validate(properties_field)

                    links_dict[area_to]["filter-synthesis"] = set(links_dict[area_to]["filter-synthesis"].split(", "))
                    links_dict[area_to]["filter-year-by-year"] = set(
                        links_dict[area_to]["filter-year-by-year"].split(", ")
                    )

                    link_properties = LinkPropertiesLocal.model_validate(links_dict[area_to])

                    link_clusters.append(
                        Link(
                            area_from=area_from,
                            area_to=area_to,
                            link_service=self,
                            properties=link_properties.yield_link_properties(),
                            ui=ui_properties.yield_link_ui(),
                        )
                    )
        return link_clusters
