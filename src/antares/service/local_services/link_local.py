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

import configparser
import os

from types import MappingProxyType
from typing import Any, Dict, Optional

from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import CustomError, LinkCreationError
from antares.model.area import Area
from antares.model.link import Link, LinkProperties, LinkPropertiesLocal, LinkUi, LinkUiLocal
from antares.service.base_services import BaseLinkService
from antares.tools.contents_tool import sort_ini_sections


class LinkLocalService(BaseLinkService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def create_link(
        self,
        area_from: Area,
        area_to: Area,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
        existing_areas: Optional[MappingProxyType[str, Area]] = None,
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
        areas = dict(sorted({area_from.name: area_from, area_to.name: area_to}.items()))

        if existing_areas is not None:
            for area in areas.keys():
                if area not in existing_areas:
                    raise LinkCreationError(area_from.name, area_to.name, f"{area} does not exist.")
        else:
            raise LinkCreationError(area_from.name, area_to.name, "Cannot verify existing areas.")

        area_from, area_to = areas.values()

        link_dir = self.config.study_path / "input/links" / area_from.name
        os.makedirs(link_dir, exist_ok=True)

        local_properties = (
            LinkPropertiesLocal.model_validate(properties.model_dump(mode="json", exclude_none=True))
            if properties
            else LinkPropertiesLocal()
        )
        local_ui = LinkUiLocal.model_validate(ui.model_dump(mode="json", exclude_none=True)) if ui else LinkUiLocal()

        properties_ini_file = link_dir / "properties.ini"
        properties_ini = configparser.ConfigParser()

        if properties_ini_file.is_file():
            with open(properties_ini_file, "r") as ini_file:
                properties_ini.read_file(ini_file)
        try:
            properties_ini.add_section(area_to.name)
        except configparser.DuplicateSectionError as e:
            raise CustomError(f"Link exists already, section already exists in properties.ini:\n\n{e.message}")
        ini_dict = dict(local_properties.ini_fields)
        ini_dict.update(local_ui.ini_fields)
        properties_ini[area_to.name] = self.sort_link_properties_dict(ini_dict)

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
