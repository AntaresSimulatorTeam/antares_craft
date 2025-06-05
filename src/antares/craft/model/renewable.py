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

from antares.craft.model.cluster import ClusterProperties, ClusterPropertiesUpdate
from antares.craft.service.base_services import BaseRenewableService
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id


class RenewableClusterGroup(EnumIgnoreCase):
    """
    Renewable cluster groups.

    The group can be any one of the following:
    "Wind Onshore", "Wind Offshore", "Solar Thermal", "Solar PV", "Solar Rooftop",
    "Other RES 1", "Other RES 2", "Other RES 3", or "Other RES 4".
    If not specified, the renewable cluster will be part of the group "Other RES 1".
    """

    THERMAL_SOLAR = "solar thermal"
    PV_SOLAR = "solar pv"
    ROOFTOP_SOLAR = "solar rooftop"
    WIND_ON_SHORE = "wind onshore"
    WIND_OFF_SHORE = "wind offshore"
    OTHER1 = "other res 1"
    OTHER2 = "other res 2"
    OTHER3 = "other res 3"
    OTHER4 = "other res 4"


class TimeSeriesInterpretation(Enum):
    """
    Timeseries mode:

    - Power generation means that the unit of the timeseries is in MW,
    - Production factor means that the unit of the timeseries is in p.u.
      (between 0 and 1, 1 meaning the full installed capacity)
    """

    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


@dataclass(frozen=True)
class RenewableClusterProperties(ClusterProperties):
    group: RenewableClusterGroup = RenewableClusterGroup.OTHER1
    ts_interpretation: TimeSeriesInterpretation = TimeSeriesInterpretation.POWER_GENERATION


@dataclass
class RenewableClusterPropertiesUpdate(ClusterPropertiesUpdate):
    group: Optional[RenewableClusterGroup] = None
    ts_interpretation: Optional[TimeSeriesInterpretation] = None


class RenewableCluster:
    def __init__(
        self,
        renewable_service: BaseRenewableService,
        area_id: str,
        name: str,
        properties: Optional[RenewableClusterProperties] = None,
    ):
        self._area_id = area_id
        self._renewable_service = renewable_service
        self._name = name
        self._id = transform_name_to_id(name)
        self._properties = properties or RenewableClusterProperties()

    @property
    def area_id(self) -> str:
        return self._area_id

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    @property
    def properties(self) -> RenewableClusterProperties:
        return self._properties

    def update_properties(self, properties: RenewableClusterPropertiesUpdate) -> RenewableClusterProperties:
        new_properties = self._renewable_service.update_renewable_clusters_properties({self: properties})
        self._properties = new_properties[self]
        return self._properties

    def get_timeseries(self) -> pd.DataFrame:
        return self._renewable_service.get_renewable_matrix(self.id, self.area_id)

    def set_series(self, matrix: pd.DataFrame) -> None:
        self._renewable_service.set_series(self, matrix)
