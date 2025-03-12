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
from configparser import DuplicateSectionError
from typing import Any, Dict, Optional

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    LinkCreationError,
    LinkDeletionError,
    LinkPropertiesUpdateError,
    LinkUiUpdateError,
)
from antares.craft.model.link import Link, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
from antares.craft.service.base_services import BaseLinkService
from antares.craft.service.local_services.models.link import LinkPropertiesAndUiLocal
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.contents_tool import sort_ini_sections
from antares.craft.tools.custom_raw_config_parser import CustomRawConfigParser
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
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

        Returns:
            The created link

        Raises:
            LinkCreationError if an area doesn't exist or existing areas have not been provided
        """

        link_dir = self.config.study_path / "input" / "links" / area_from
        link_dir.mkdir(parents=True, exist_ok=True)
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

        # Creates empty matrices
        series = pd.DataFrame()
        for ts in [
            TimeSeriesFileType.LINKS_PARAMETERS,
            TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT,
            TimeSeriesFileType.LINKS_CAPACITIES_DIRECT,
        ]:
            write_timeseries(self.config.study_path, series, ts, area_id=area_from, second_area_id=area_to)

        return Link(
            area_from=area_from,
            area_to=area_to,
            link_service=self,
            properties=local_model.to_properties_user_model(),  # round-trip for pydantic validation
            ui=local_model.to_ui_user_model(),
        )

    @override
    def delete_link(self, link: Link) -> None:
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.LINK_PROPERTIES_INI, link.area_from_id)
        links_dict = ini_file.ini_dict
        for area_to, link_props in links_dict.items():
            if area_to == link.area_to_id:
                links_dict.pop(area_to)
                ini_file.ini_dict = links_dict
                ini_file.write_ini_file()
                return

        raise LinkDeletionError(link.id, "it doesn't exist")

    def _update_link(
        self, link: Link, properties: Optional[LinkPropertiesUpdate] = None, ui: Optional[LinkUiUpdate] = None
    ) -> Optional[LinkPropertiesAndUiLocal]:
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.LINK_PROPERTIES_INI, link.area_from_id)
        links_dict = ini_file.ini_dict
        for area_to, link_props in links_dict.items():
            if area_to == link.area_to_id:
                # Update properties
                upd_properties = LinkPropertiesAndUiLocal.from_user_model(ui, properties)
                upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_none=True)
                link_props.update(upd_props_as_dict)

                # Update ini file
                ini_file.ini_dict = links_dict
                ini_file.write_ini_file()

                # Prepare the object to return
                return LinkPropertiesAndUiLocal.model_validate(link_props)
        return None

    @override
    def update_link_properties(self, link: Link, properties: LinkPropertiesUpdate) -> LinkProperties:
        local_properties = self._update_link(link, properties, None)
        if not local_properties:
            raise LinkPropertiesUpdateError(link.id, "The link does not exist")
        return local_properties.to_properties_user_model()

    @override
    def update_link_ui(self, link: Link, ui: LinkUiUpdate) -> LinkUi:
        local_properties = self._update_link(link, None, ui)
        if not local_properties:
            raise LinkUiUpdateError(link.id, "The link does not exist")
        return local_properties.to_ui_user_model()

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
    def set_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        checks_matrix_dimensions(series, f"links/{area_from}/{area_to}", "links_parameters")
        write_timeseries(
            self.config.study_path,
            series,
            TimeSeriesFileType.LINKS_PARAMETERS,
            area_id=area_from,
            second_area_id=area_to,
        )

    @override
    def set_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        checks_matrix_dimensions(series, f"links/{area_from}/{area_to}", "series")
        write_timeseries(
            self.config.study_path,
            series,
            TimeSeriesFileType.LINKS_CAPACITIES_DIRECT,
            area_id=area_from,
            second_area_id=area_to,
        )

    @override
    def set_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        checks_matrix_dimensions(series, f"links/{area_from}/{area_to}", "series")
        write_timeseries(
            self.config.study_path,
            series,
            TimeSeriesFileType.LINKS_CAPACITIES_INDIRECT,
            area_id=area_from,
            second_area_id=area_to,
        )

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
        new_properties_dict = {}
        for link_name, update_properties in dict_links.items():
            area_from, area_to = link_name.split(" / ")
            link = Link(area_from, area_to, link_service=self)
            new_properties = self.update_link_properties(link, update_properties)
            new_properties_dict[link.id] = new_properties
        return new_properties_dict
