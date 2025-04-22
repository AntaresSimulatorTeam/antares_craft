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

from typing_extensions import override

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
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType


class LinkLocalService(BaseLinkService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def _read_ini(self, area_from: str) -> dict[str, Any]:
        return IniReader().read(self.config.study_path / "input" / "links" / area_from / "properties.ini")

    def _save_ini(self, content: dict[str, Any], area_from: str) -> None:
        IniWriter().write(content, self.config.study_path / "input" / "links" / area_from / "properties.ini")

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

        current_content = self._read_ini(area_from)

        if area_to in current_content:
            raise LinkCreationError(
                area_from=area_from,
                area_to=area_to,
                message=f"Link exists already between '{area_from}' and '{area_to}'.",
            )

        new_properties = local_model.model_dump(mode="json", by_alias=True)
        current_content[area_to] = new_properties
        self._save_ini(current_content, area_from)

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
        links_dict = self._read_ini(link.area_from_id)
        for area_to, link_props in links_dict.items():
            if area_to == link.area_to_id:
                links_dict.pop(area_to)
                self._save_ini(links_dict, link.area_from_id)
                return

        raise LinkDeletionError(link.id, "it doesn't exist")

    @override
    def update_link_ui(self, link: Link, ui: LinkUiUpdate) -> LinkUi:
        links_dict = self._read_ini(link.area_from_id)
        for area_to, link_props in links_dict.items():
            if area_to == link.area_to_id:
                # Update properties
                upd_properties = LinkPropertiesAndUiLocal.from_user_model(ui, None)
                upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_unset=True)
                link_props.update(upd_props_as_dict)

                # Update ini file
                self._save_ini(links_dict, link.area_from_id)

                # Prepare the object to return
                return LinkPropertiesAndUiLocal.model_validate(link_props).to_ui_user_model()

        raise LinkUiUpdateError(link.id, "The link does not exist")

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
    def read_links(self) -> dict[str, Link]:
        link_path = self.config.study_path / "input" / "links"

        all_links: dict[str, Link] = {}

        for element in link_path.iterdir():
            area_from = element.name
            links_dict = self._read_ini(area_from)
            for area_to, values in links_dict.items():
                local_model = LinkPropertiesAndUiLocal.model_validate(values)
                properties = local_model.to_properties_user_model()
                ui = local_model.to_ui_user_model()
                link = Link(area_from=area_from, area_to=area_to, link_service=self, properties=properties, ui=ui)
                all_links[link.id] = link

        return all_links

    @override
    def update_links_properties(self, new_properties: dict[str, LinkPropertiesUpdate]) -> dict[str, LinkProperties]:
        new_properties_dict: dict[str, LinkProperties] = {}

        properties_by_areas: dict[str, dict[str, LinkPropertiesUpdate]] = {}
        for link_id, properties in new_properties.items():
            area_from, area_to = link_id.split(" / ")
            properties_by_areas.setdefault(area_from, {})[area_to] = properties

        for area_from, value in properties_by_areas.items():
            all_link_names = set(value.keys())  # used to raise an Exception if a link doesn't exist
            current_dict = self._read_ini(area_from)
            for area_to, link_properties_dict in current_dict.items():
                if area_to in value:
                    all_link_names.remove(area_to)
                    # Update properties
                    upd_properties = LinkPropertiesAndUiLocal.from_user_model(None, value[area_to])
                    upd_props_as_dict = upd_properties.model_dump(mode="json", by_alias=True, exclude_unset=True)
                    link_properties_dict.update(upd_props_as_dict)

                    # Prepare the object to return
                    link_properties_obj = LinkPropertiesAndUiLocal.model_validate(link_properties_dict)
                    new_properties_dict[f"{area_from} / {area_to}"] = link_properties_obj.to_properties_user_model()

            if len(all_link_names) > 0:
                raise LinkPropertiesUpdateError(next(iter(all_link_names)), self.study_name, "The link does not exist")

            # Update ini file
            self._save_ini(current_dict, area_from)

        return new_properties_dict
