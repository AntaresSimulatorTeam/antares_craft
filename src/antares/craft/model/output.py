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
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd

from antares.craft.service.base_services import BaseOutputService


class MCIndAreasDataType(Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreasDataType(Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinksDataType(Enum):
    VALUES = "values"


class MCAllLinksDataType(Enum):
    VALUES = "values"
    ID = "id"


class Frequency(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


@dataclass
class AggregationEntry:
    """
    Represents an entry for aggregation queries

    Attributes:
        frequency: "hourly", "daily", "weekly", "monthly", "annual"
        mc_years: Monte Carlo years to include in the query. If left empty, all years are included.
        type_ids: which links/areas to be selected (ex: "be - fr"). If empty, all are selected
        columns_names: names or regexes (if data_type is of type details) to select columns
    """

    data_type: MCAllAreasDataType | MCIndAreasDataType | MCAllLinksDataType | MCIndLinksDataType
    frequency: Frequency
    mc_years: Optional[list[int]] = None
    type_ids: Optional[list[str]] = None
    columns_names: Optional[list[str]] = None

    def to_api_query(self, object_type: str) -> str:
        mc_years = f"&mc_years={','.join(str(year) for year in self.mc_years)}" if self.mc_years else ""
        type_ids = f"&{object_type}_ids={','.join(self.type_ids)}" if self.type_ids else ""
        columns_names = f"&columns_names={','.join(self.columns_names)}" if self.columns_names else ""

        return f"query_file={self.data_type.value}&frequency={self.frequency.value}{mc_years}{type_ids}{columns_names}&format=csv"


class Output:
    def __init__(self, name: str, archived: bool, output_service: BaseOutputService):
        self._name = name
        self._archived = archived
        self._output_service: BaseOutputService = output_service

    @property
    def name(self) -> str:
        return self._name

    @property
    def archived(self) -> bool:
        return self._archived

    def get_mc_all_area(self, frequency: Frequency, data_type: MCAllAreasDataType, area: str) -> pd.DataFrame:
        """

        Args:
            frequency: "hourly", "daily", "weekly", "monthly", "annual"
            data_type: the data-type of mc-all areas
            area: the area name

        Returns:

        """
        file_path = f"mc-all/areas/{area}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_all_link(
        self, frequency: Frequency, data_type: MCAllLinksDataType, area_from: str, area_to: str
    ) -> pd.DataFrame:
        """

        Args:
            frequency: "hourly", "daily", "weekly", "monthly", "annual"
            data_type: the data-type of mc-all links
            area_from: area_from id
            area_to: area_to id

        Returns:

        """
        area_from, area_to = sorted([area_from, area_to])
        file_path = f"mc-all/links/{area_from} - {area_to}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_ind_area(
        self, mc_year: int, frequency: Frequency, data_type: MCIndAreasDataType, area: str
    ) -> pd.DataFrame:
        """

        Args:
            mc_year:
            frequency: "hourly", "daily", "weekly", "monthly", "annual"
            data_type: the data-type of mc-ind areas
            area: the area name

        Returns:

        """
        file_path = f"mc-ind/{mc_year:05}/areas/{area}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def get_mc_ind_link(
        self, mc_year: int, frequency: Frequency, data_type: MCIndLinksDataType, area_from: str, area_to: str
    ) -> pd.DataFrame:
        """

        Args:
            mc_year:
            frequency: "hourly", "daily", "weekly", "monthly", "annual"
            data_type: the data-type of mc-ind links
            area_from: area_from id
            area_to: area_to id

        Returns:

        """
        area_from, area_to = sorted([area_from, area_to])
        file_path = f"mc-ind/{mc_year:05}/links/{area_from} - {area_to}/{data_type.value}-{frequency.value}"
        return self._output_service.get_matrix(self.name, file_path, frequency)

    def aggregate_mc_ind_areas(
        self,
        data_type: MCIndAreasDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for areas with mc-ind

        Args:
            data_type: values from McIndAreasDataType
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "ind")

    def aggregate_mc_ind_links(
        self,
        data_type: MCIndLinksDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        links_ids: Optional[list[tuple[str, str]]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for links with mc-ind

        Args:
            data_type: values from McIndLinks
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        type_ids = (
            [f"{area_from} - {area_to}" for link_id in links_ids for area_from, area_to in [sorted(link_id)]]
            if links_ids
            else None
        )

        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=type_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "ind")

    def aggregate_mc_all_areas(
        self,
        data_type: MCAllAreasDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for areas with mc-all

        Args:
            data_type: values from McAllAreas
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "all")

    def aggregate_mc_all_links(
        self,
        data_type: MCAllLinksDataType,
        frequency: Frequency,
        mc_years: Optional[list[int]] = None,
        links_ids: Optional[list[tuple[str, str]]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for links with mc-all

        Args:
            data_type: values from McAllLinks
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        type_ids = (
            [f"{area_from} - {area_to}" for link_id in links_ids for area_from, area_to in [sorted(link_id)]]
            if links_ids
            else None
        )

        aggregation_entry = AggregationEntry(
            data_type=data_type,
            frequency=frequency,
            mc_years=mc_years,
            type_ids=type_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "all")
