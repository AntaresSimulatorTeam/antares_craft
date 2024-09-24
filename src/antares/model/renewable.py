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
from typing import Optional, Any

import pandas as pd
from pydantic import BaseModel, computed_field

from antares.model.cluster import ClusterProperties
from antares.tools.contents_tool import transform_name_to_id


class RenewableClusterGroup(Enum):
    """
    Renewable cluster groups.

    The group can be any one of the following:
    "Wind Onshore", "Wind Offshore", "Solar Thermal", "Solar PV", "Solar Rooftop",
    "Other RES 1", "Other RES 2", "Other RES 3", or "Other RES 4".
    If not specified, the renewable cluster will be part of the group "Other RES 1".
    """

    THERMAL_SOLAR = "Solar Thermal"
    PV_SOLAR = "Solar PV"
    ROOFTOP_SOLAR = "Solar Rooftop"
    WIND_ON_SHORE = "Wind Onshore"
    WIND_OFF_SHORE = "Wind Offshore"
    OTHER1 = "Other RES 1"
    OTHER2 = "Other RES 2"
    OTHER3 = "Other RES 3"
    OTHER4 = "Other RES 4"


class TimeSeriesInterpretation(Enum):
    """
    Timeseries mode:

    - Power generation means that the unit of the timeseries is in MW,
    - Production factor means that the unit of the timeseries is in p.u.
      (between 0 and 1, 1 meaning the full installed capacity)
    """

    POWER_GENERATION = "power-generation"
    PRODUCTION_FACTOR = "production-factor"


class RenewableClusterProperties(ClusterProperties):
    """
    Properties of a renewable cluster read from the configuration files.
    """

    group: Optional[RenewableClusterGroup] = None
    ts_interpretation: Optional[TimeSeriesInterpretation] = None


# TODO update to use check_if_none
class RenewableClusterPropertiesLocal(
    BaseModel,
):
    def __init__(
        self,
        renewable_name: str,
        renewable_cluster_properties: Optional[RenewableClusterProperties] = None,
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        renewable_cluster_properties = renewable_cluster_properties or RenewableClusterProperties()
        self._renewable_name = renewable_name
        self._enabled = (
            renewable_cluster_properties.enabled if renewable_cluster_properties.enabled is not None else True
        )
        self._unit_count = (
            renewable_cluster_properties.unit_count if renewable_cluster_properties.unit_count is not None else 1
        )
        self._nominal_capacity = (
            renewable_cluster_properties.nominal_capacity
            if renewable_cluster_properties.nominal_capacity is not None
            else 0
        )
        self._group = renewable_cluster_properties.group or RenewableClusterGroup.OTHER1
        self._ts_interpretation = (
            renewable_cluster_properties.ts_interpretation or TimeSeriesInterpretation.POWER_GENERATION
        )

    @property
    def renewable_name(self) -> str:
        return self._renewable_name

    @computed_field  # type: ignore[misc]
    @property
    def ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            self._renewable_name: {
                "name": self._renewable_name,
                "group": self._group.value,
                "enabled": f"{self._enabled}".lower(),
                "nominalcapacity": f"{self._nominal_capacity:.6f}",
                "unitcount": f"{self._unit_count}",
                "ts-interpretation": self._ts_interpretation.value,
            }
        }

    def yield_renewable_cluster_properties(self) -> RenewableClusterProperties:
        return RenewableClusterProperties(
            enabled=self._enabled,
            unit_count=self._unit_count,
            nominal_capacity=self._nominal_capacity,
            group=self._group,
            ts_interpretation=self._ts_interpretation,
        )


class RenewableCluster:
    def __init__(  # type: ignore  # TODO: Find a way to avoid circular imports
        self,
        renewable_service,
        area_id: str,
        name: str,
        properties: Optional[RenewableClusterProperties] = None,
    ):
        self._area_id = area_id
        self._renewable_service = renewable_service
        self._name = name
        self._id = transform_name_to_id(name)
        self._properties = properties or RenewableClusterProperties()

    # TODO: Add matrices.

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

    def update_properties(self, properties: RenewableClusterProperties) -> None:
        new_properties = self._renewable_service.update_renewable_properties(self, properties)
        self._properties = new_properties

    def get_renewable_matrix(self) -> pd.DataFrame:
        return self._renewable_service.get_renewable_matrix(self)
