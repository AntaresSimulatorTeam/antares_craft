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
from typing import Optional, Union

import pandas as pd

from antares.craft.service.base_services import BaseOutputService


class MCIndAreas(Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class MCAllAreas(Enum):
    VALUES = "values"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"
    ID = "id"


class MCIndLinks(Enum):
    VALUES = "values"


class MCAllLinks(Enum):
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
        columns_names: names or regexes (if query_file is of type details) to select columns
    """

    query_file: Union[MCAllAreas, MCIndAreas, MCAllLinks, MCIndLinks]
    frequency: Frequency
    mc_years: Optional[list[str]] = None
    type_ids: Optional[list[str]] = None
    columns_names: Optional[list[str]] = None

    def to_api_query(self, object_type: str) -> str:
        mc_years = f"&mc_years={','.join(self.mc_years)}" if self.mc_years else ""
        type_ids = f"&{object_type}_ids={','.join(self.type_ids)}" if self.type_ids else ""
        columns_names = f"&columns_names={','.join(self.columns_names)}" if self.columns_names else ""

        return f"query_file={self.query_file.value}&frequency={self.frequency.value}{mc_years}{type_ids}{columns_names}&format=csv"


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

    def get_matrix(self, path: str) -> pd.DataFrame:
        """
        Gets the matrix of the output

        Args:
            path: output path, eg: "mc-all/areas/south/values-hourly"

        Returns: Pandas DataFrame
        """
        return self._output_service.get_matrix(self.name, path)

    def aggregate_areas_mc_ind(
        self,
        query_file: str,
        frequency: str,
        mc_years: Optional[list[str]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for areas with mc-ind

        Args:
            query_file: values from McIndAreas
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            query_file=MCIndAreas(query_file),
            frequency=Frequency(frequency),
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "ind")

    def aggregate_links_mc_ind(
        self,
        query_file: str,
        frequency: str,
        mc_years: Optional[list[str]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for links with mc-ind

        Args:
            query_file: values from McIndLinks
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            query_file=MCIndLinks(query_file),
            frequency=Frequency(frequency),
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "ind")

    def aggregate_areas_mc_all(
        self,
        query_file: str,
        frequency: str,
        mc_years: Optional[list[str]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for areas with mc-all

        Args:
            query_file: values from McAllAreas
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            query_file=MCAllAreas(query_file),
            frequency=Frequency(frequency),
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "areas", "all")

    def aggregate_links_mc_all(
        self,
        query_file: str,
        frequency: str,
        mc_years: Optional[list[str]] = None,
        areas_ids: Optional[list[str]] = None,
        columns_names: Optional[list[str]] = None,
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data for links with mc-all

        Args:
            query_file: values from McAllLinks
            frequency: values from Frequency

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        aggregation_entry = AggregationEntry(
            query_file=MCAllLinks(query_file),
            frequency=Frequency(frequency),
            mc_years=mc_years,
            type_ids=areas_ids,
            columns_names=columns_names,
        )

        return self._output_service.aggregate_values(self.name, aggregation_entry, "links", "all")
