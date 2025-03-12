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

from antares.craft.service.base_services import BaseShortTermStorageService
from antares.craft.tools.contents_tool import transform_name_to_id


class STStorageGroup(Enum):
    # todo: this class should disappear with Simulator version 9.1
    PSP_OPEN = "psp_open"
    PSP_CLOSED = "psp_closed"
    PONDAGE = "pondage"
    BATTERY = "battery"
    OTHER1 = "other1"
    OTHER2 = "other2"
    OTHER3 = "other3"
    OTHER4 = "other4"
    OTHER5 = "other5"


class STStorageMatrixName(Enum):
    PMAX_INJECTION = "pmax_injection"
    PMAX_WITHDRAWAL = "pmax_withdrawal"
    LOWER_CURVE_RULE = "lower_rule_curve"
    UPPER_RULE_CURVE = "upper_rule_curve"
    INFLOWS = "inflows"


@dataclass
class STStoragePropertiesUpdate:
    group: Optional[STStorageGroup] = None
    injection_nominal_capacity: Optional[float] = None
    withdrawal_nominal_capacity: Optional[float] = None
    reservoir_capacity: Optional[float] = None
    efficiency: Optional[float] = None
    initial_level: Optional[float] = None
    initial_level_optim: Optional[bool] = None
    enabled: Optional[bool] = None


@dataclass(frozen=True)
class STStorageProperties:
    group: STStorageGroup = STStorageGroup.OTHER1
    injection_nominal_capacity: float = 0
    withdrawal_nominal_capacity: float = 0
    reservoir_capacity: float = 0
    efficiency: float = 1
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True


class STStorage:
    def __init__(
        self,
        storage_service: BaseShortTermStorageService,
        area_id: str,
        name: str,
        properties: Optional[STStorageProperties] = None,
    ):
        self._area_id: str = area_id
        self._storage_service: BaseShortTermStorageService = storage_service
        self._name: str = name
        self._id: str = transform_name_to_id(name)
        self._properties: STStorageProperties = properties or STStorageProperties()

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

    def update_properties(self, properties: STStoragePropertiesUpdate) -> STStorageProperties:
        new_properties = self._storage_service.update_st_storage_properties(self, properties)
        self._properties = new_properties
        return self._properties

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

    def update_pmax_injection(self, p_max_injection_matrix: pd.DataFrame) -> None:
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.PMAX_INJECTION, p_max_injection_matrix)

    def set_pmax_withdrawal(self, p_max_withdrawal_matrix: pd.DataFrame) -> None:
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.PMAX_WITHDRAWAL, p_max_withdrawal_matrix)

    def set_lower_rule_curve(self, lower_rule_curve_matrix: pd.DataFrame) -> None:
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.LOWER_CURVE_RULE, lower_rule_curve_matrix)

    def set_upper_rule_curve(self, upper_rule_curve_matrix: pd.DataFrame) -> None:
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.UPPER_RULE_CURVE, upper_rule_curve_matrix)

    def set_storage_inflows(self, inflows_matrix: pd.DataFrame) -> None:
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.INFLOWS, inflows_matrix)
