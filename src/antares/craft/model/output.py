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
from enum import Enum
from typing import Any

import pandas as pd

from pydantic import BaseModel, Field


class QueryFile(Enum):
    VALUES = "values"
    ID = "id"
    DETAILS = "details"
    DETAILS_ST_STORAGE = "details-STstorage"
    DETAILS_RES = "details-res"


class Frequency(Enum):
    HOURLY = "hourly"
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    ANNUAL = "annual"


class McType(Enum):
    ALL = "mc-all"
    IND = "mc-ind"


class ObjectType(Enum):
    LINKS = "links"
    AREAS = "areas"


class AggregationEntry(BaseModel):
    """
    Represents an entry for aggregation queries

    Attributes:
        query_file: The file to query.
        frequency: "hourly", "daily", "weekly", "monthly", "annual"
        mc_years: Monte Carlo years to include in the query. If left empty, all years are included.
        type_ids: which links/areas to be selected (ex: "be - fr"). If empty, all are selected
        columns_names: names or regexes (if query_file is of type details) to select columns
    """

    query_file: QueryFile
    frequency: Frequency
    mc_years: list[str] = Field(default_factory=list)
    type_ids: list[str] = Field(default_factory=list)
    columns_names: list[str] = Field(default_factory=list)

    def to_api_query(self, object_type: ObjectType) -> str:
        mc_years = f"&mc_years={','.join(self.mc_years)}" if self.mc_years else ""
        type_ids = f"&{object_type.value}_ids={','.join(self.type_ids)}" if self.type_ids else ""
        columns_names = f"&columns_names={','.join(self.columns_names)}" if self.columns_names else ""

        return f"query_file={self.query_file.value}&frequency={self.frequency.value}{mc_years}{type_ids}{columns_names}&format=csv"


class Output:
    def __init__(self, name: str, archived: bool, output_service):  # type: ignore
        self._name = name
        self._archived = archived
        self._output_service = output_service

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Output):
            return self._name == other._name and self._archived == other._archived
        return False

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
        full_path = f"output/{self.name}/economy/{path}"
        return self._output_service.get_matrix(full_path)

    def aggregate_values(
        self, aggregation_entry: AggregationEntry, mc_type: McType, object_type: ObjectType
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data

        Args:
            aggregate_input: input for the /aggregate endpoint
            mc_type: all or ind (enum)
            object_type: links or area (enum)

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        return self._output_service.aggregate_values(self.name, aggregation_entry, mc_type, object_type)
