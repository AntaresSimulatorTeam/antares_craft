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
from pydantic.alias_generators import to_camel

from antares.tools.contents_tool import transform_name_to_id
from antares.tools.ini_tool import check_if_none


class STStorageGroup(Enum):
    # todo: this class should disappear with Simulator version 9.1
    PSP_OPEN = "PSP_open"
    PSP_CLOSED = "PSP_closed"
    PONDAGE = "Pondage"
    BATTERY = "Battery"
    OTHER1 = "Other1"
    OTHER2 = "Other2"
    OTHER3 = "Other3"
    OTHER4 = "Other4"
    OTHER5 = "Other5"


class STStorageMatrixName(Enum):
    PMAX_INJECTION = "pmax_injection"
    PMAX_WITHDRAWAL = "pmax_withdrawal"
    LOWER_CURVE_RULE = "lower_rule_curve"
    UPPER_RULE_CURVE = "upper_rule_curve"
    INFLOWS = "inflows"


class STStorageProperties(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    """
    Properties of a short-term storage system read from the configuration files.

    All aliases match the name of the corresponding field in the INI files.
    """

    group: Optional[STStorageGroup] = None
    injection_nominal_capacity: Optional[float] = None
    withdrawal_nominal_capacity: Optional[float] = None
    reservoir_capacity: Optional[float] = None
    efficiency: Optional[float] = None
    initial_level: Optional[float] = None
    initial_level_optim: Optional[bool] = None
    # v880
    enabled: Optional[bool] = None


class STStoragePropertiesLocal(BaseModel):
    def __init__(
        self,
        st_storage_name: str,
        st_storage_properties: Optional[STStorageProperties] = None,
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        st_storage_properties = st_storage_properties or STStorageProperties()
        self._st_storage_name = st_storage_name
        self._group = check_if_none(st_storage_properties.group, STStorageGroup.OTHER1)
        self._injection_nominal_capacity = check_if_none(st_storage_properties.injection_nominal_capacity, 0)
        self._withdrawal_nominal_capacity = check_if_none(st_storage_properties.withdrawal_nominal_capacity, 0)
        self._reservoir_capacity = check_if_none(st_storage_properties.reservoir_capacity, 0)
        self._efficiency = check_if_none(st_storage_properties.efficiency, 1)
        self._initial_level = check_if_none(st_storage_properties.initial_level, 0.5)
        self._initial_level_optim = check_if_none(st_storage_properties.initial_level_optim, False)
        self._enabled = check_if_none(st_storage_properties.enabled, True)

    @property
    def st_storage_name(self) -> str:
        return self._st_storage_name

    @computed_field  # type: ignore[misc]
    @property
    def list_ini_fields(self) -> dict[str, dict[str, str]]:
        return {
            f"{self._st_storage_name}": {
                "name": self._st_storage_name,
                "group": self._group.value,
                "injectionnominalcapacity": f"{self._injection_nominal_capacity:.6f}",
                "withdrawalnominalcapacity": f"{self._withdrawal_nominal_capacity:.6f}",
                "reservoircapacity": f"{self._reservoir_capacity:.6f}",
                "efficiency": f"{self._efficiency:.6f}",
                "initiallevel": f"{self._initial_level:.6f}",
                "initialleveloptim": f"{self._initial_level_optim}".lower(),
                "enabled": f"{self._enabled}".lower(),
            }
        }

    def yield_st_storage_properties(self) -> STStorageProperties:
        return STStorageProperties(
            group=self._group,
            injection_nominal_capacity=self._injection_nominal_capacity,
            withdrawal_nominal_capacity=self._withdrawal_nominal_capacity,
            reservoir_capacity=self._reservoir_capacity,
            efficiency=self._efficiency,
            initial_level=self._initial_level,
            initial_level_optim=self._initial_level_optim,
            enabled=self._enabled,
        )


class STStorage:
    def __init__(self, storage_service, area_id: str, name: str, properties: Optional[STStorageProperties] = None):  # type: ignore # TODO: Find a way to avoid circular imports
        self._area_id = area_id
        self._storage_service = storage_service
        self._name = name
        self._id = transform_name_to_id(name)
        self._properties = properties or STStorageProperties()

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
    def properties(self) -> STStorageProperties:
        return self._properties

    def update_properties(self, properties: STStorageProperties) -> None:
        new_properties = self._storage_service.update_st_storage_properties(self, properties)
        self._properties = new_properties

    def get_pmax_injection(self) -> pd.DataFrame:
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.PMAX_INJECTION)

    def get_pmax_withdrawal(self) -> pd.DataFrame:
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.PMAX_WITHDRAWAL)

    def get_lower_rule_curve(self) -> pd.DataFrame:
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.LOWER_CURVE_RULE)

    def get_upper_rule_curve(self) -> pd.DataFrame:
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.UPPER_RULE_CURVE)

    def get_storage_inflows(self) -> pd.DataFrame:
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.INFLOWS)

    def upload_pmax_injection(self, p_max_injection_matrix: pd.DataFrame) -> None:
        return self._storage_service.upload_storage_matrix(
            self, STStorageMatrixName.PMAX_INJECTION, p_max_injection_matrix
        )

    def upload_pmax_withdrawal(self, p_max_withdrawal_matrix: pd.DataFrame) -> None:
        return self._storage_service.upload_storage_matrix(
            self, STStorageMatrixName.PMAX_WITHDRAWAL, p_max_withdrawal_matrix
        )

    def upload_lower_rule_curve(self, lower_rule_curve_matrix: pd.DataFrame) -> None:
        return self._storage_service.upload_storage_matrix(
            self, STStorageMatrixName.LOWER_CURVE_RULE, lower_rule_curve_matrix
        )

    def upload_upper_rule_curve(self, upper_rule_curve_matrix: pd.DataFrame) -> None:
        return self._storage_service.upload_storage_matrix(
            self, STStorageMatrixName.UPPER_RULE_CURVE, upper_rule_curve_matrix
        )

    def upload_storage_inflows(self, inflows_matrix: pd.DataFrame) -> None:
        return self._storage_service.upload_storage_matrix(self, STStorageMatrixName.INFLOWS, inflows_matrix)