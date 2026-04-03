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
from dataclasses import dataclass, field
from enum import Enum
from types import MappingProxyType
from typing import Optional

import pandas as pd

from antares.craft.service.base_services import BaseShortTermStorageService
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id


class STStorageGroup(EnumIgnoreCase):
    """Short-term storage group possibilities.

    Attributes:
        PSP_OPEN: Open cycle Pump-Storage Plants.
        PSP_CLOSED: Closed cycle Pump-Storage Plants.
        PONDAGE: Small water storage behind the weir of a
            run-of-the-river hydroelectric power plant
        BATTERY: Battery.
        OTHER1: Other 1.
        OTHER2: Other 2.
        OTHER3: Other 3.
        OTHER4: Other 4.
        OTHER5: Other 5.
    """

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
    """Short-term storage matrix column headers.

    Attributes:
        PMAX_INJECTION: Maximum power injection involving modulation of the
            injection capacity each hour, reflecting lower availability of
            the storage at certain times (planned or forced outages).
        PMAX_WITHDRAWAL: Maximum power withdrawal involving modulation of the
            injection capacity each hour, reflecting lower availability of
            the storage at certain times (planned or forced outages).
        LOWER_CURVE_RULE: Lower limit for filling the stock,
            expressed as a filling rate, imposed each hour.
        UPPER_RULE_CURVE: Upper limit for filling the stock,
            expressed as a filling rate, imposed each hour.
        INFLOWS: Natural inflows in MW that enters into the storage. The values
            for this file can be negative, corresponding to withdrawals imposed on the stock for other uses
        COST_INJECTION: **Introduced in v9.2.** Penalization of the injection flowrate at each hour in €/MW.
        COST_WITHDRAWAL: **Introduced in v9.2.** Penalization of the withdrawal flowrate at each hour in €/MW.
        COST_LEVEL: **Introduced in v9.2.** Penalization of the volume of stored energy at each hour in €/MWh.
            A negative penalty is allowed for this cost. If the penalty is positive,
            it will favor lower-level trajectories. If the penalty is negative, it will favor higher-level trajectories.
        COST_VARIATION_INJECTION: **Introduced in v9.2.** Penalizes the injection flowrate variation every hour in €/MW/h.
            This penalty must be positive. This penalty is only enabled if the boolean parameter `penalize-variation-injection`
            is set to `True`. This penalty will penalize proportionally any injection flowrate variation between 2 hours.
        COST_VARIATION_WITHDRAWAL: **Introduced in v9.2.** Penalizes the withdrawal flowrate variation every hour in €/MW/h.
            This penalty must be positive. This penalty is only enabled if the boolean parameter `penalize_variation_withdrawal`
            is set to `True`. This penalty will penalize proportionally any withdrawal flowrate variation between 2 hours.
    """

    PMAX_INJECTION = "pmax_injection"
    PMAX_WITHDRAWAL = "pmax_withdrawal"
    LOWER_CURVE_RULE = "lower_rule_curve"
    UPPER_RULE_CURVE = "upper_rule_curve"
    INFLOWS = "inflows"
    # NEW TS name v9.2
    COST_INJECTION = "cost_injection"
    COST_WITHDRAWAL = "cost_withdrawal"
    COST_LEVEL = "cost_level"
    COST_VARIATION_INJECTION = "cost_variation_injection"
    COST_VARIATION_WITHDRAWAL = "cost_variation_withdrawal"


@dataclass
class STStoragePropertiesUpdate:
    """Short-term storage properties update.

    Attributes:
        group: Group of short term storage (`PSP_OPEN`, `PSP_CLOSED`, `PONDAGE`, `BATTERY` or `OTHER`).
        injection_nominal_capacity: The maximal flow in MW that can be injected into the storage.
        withdrawal_nominal_capacity: The maximal flow in MW that can be withdraw from the storage.
        reservoir_capacity: The maximal capacity in MWh of the storage.
        efficiency: The injection energy efficiency which is the ratio between
            the stored energy and the energy taken from the system.
        initial_level: To be considered only if `initial_level_optim = False`,
            in this case corresponds to the ratio of the storage level between empty `0` and full `1`.
        initial_level_optim: Whether to allow reoptimization of the initial storage level each week.
            In this case the level is discontinuous between weeks.
            Otherwise, the initial level is imposed by the user and is identical each week.
        enabled: Whether the storage is included in the model.
        efficiency_withdrawal: The withdrawal energy efficiency which is the ratio between
            the stored energy and the energy returned to the system.
        penalize_variation_injection: Whether to create new variables to penalize the variation in the injection flowrate.
        penalize_variation_withdrawal: Whether to create new variables to penalize the variation in the withdrawal flowrate.
        allow_overflow: Whether to allow overflow of the storage.
    """

    group: Optional[str] = None
    injection_nominal_capacity: Optional[float] = None
    withdrawal_nominal_capacity: Optional[float] = None
    reservoir_capacity: Optional[float] = None
    efficiency: Optional[float] = None
    initial_level: Optional[float] = None
    initial_level_optim: Optional[bool] = None
    enabled: Optional[bool] = None
    # Introduced in v9.2
    efficiency_withdrawal: Optional[float] = None
    penalize_variation_injection: Optional[bool] = None
    penalize_variation_withdrawal: Optional[bool] = None
    # Introduced in v9.3
    allow_overflow: Optional[bool] = None


@dataclass(frozen=True)
class STStorageProperties:
    """Short-term storage properties.

    Attributes:
        group: Group of short term storage (`PSP_OPEN`, `PSP_CLOSED`, `PONDAGE`, `BATTERY` or `OTHER`).
        injection_nominal_capacity: The maximal flow in MW that can be injected into the storage.
        withdrawal_nominal_capacity: The maximal flow in MW that can be withdraw from the storage.
        reservoir_capacity: The maximal capacity in MWh of the storage.
        efficiency: The injection energy efficiency which is the ratio between
            the stored energy and the energy taken from the system.
        initial_level: To be considered only if `initial_level_optim = False`,
            in this case corresponds to the ratio of the storage level between empty `0` and full `1`.
        initial_level_optim: Whether to allow reoptimization of the initial storage level each week.
            In this case the level is discontinuous between weeks.
            Otherwise, the initial level is imposed by the user and is identical each week.
        enabled: Whether the storage is included in the model.
        efficiency_withdrawal: The withdrawal energy efficiency which is the ratio between
            the stored energy and the energy returned to the system.
        penalize_variation_injection: Whether to create new variables to penalize the variation in the injection flowrate.
        penalize_variation_withdrawal: Whether to create new variables to penalize the variation in the withdrawal flowrate.
        allow_overflow: Whether to allow overflow of the storage.
    """

    group: str = STStorageGroup.OTHER1.value
    injection_nominal_capacity: float = 0
    withdrawal_nominal_capacity: float = 0
    reservoir_capacity: float = 0
    efficiency: float = 1
    initial_level: float = 0.5
    initial_level_optim: bool = False
    enabled: bool = True
    # Introduced in v9.2
    efficiency_withdrawal: Optional[float] = None  # default 1.0
    penalize_variation_injection: Optional[bool] = None  # default False
    penalize_variation_withdrawal: Optional[bool] = None  # default False
    # Introduced in v9.3
    allow_overflow: Optional[bool] = None  # default False


class AdditionalConstraintVariable(EnumIgnoreCase):
    """Variables considered for the constraint.

    Attributes:
        WITHDRAWAL: The constraint considers a set of withdrawal values.
        INJECTION: The constraint considers a set of injection values.
        NETTING: The constraint consider a set of hybrid variables equivalent to
            the variation of the level when there are no inflows.
    """

    WITHDRAWAL = "withdrawal"
    INJECTION = "injection"
    NETTING = "netting"


class AdditionalConstraintOperator(EnumIgnoreCase):
    """Possible constraint operators.

    Attributes:
        LESS: less than (<).
        GREATER: greater than (>).
        EQUAL: equal to (=).
    """

    LESS = "less"
    GREATER = "greater"
    EQUAL = "equal"


@dataclass(frozen=True)
class Occurrence:
    """Occurence of the additional constraint.

    Attributes:
        hours: List of the index of the hours in the week where
            a constraint is applied.
    """

    hours: list[int]


@dataclass(frozen=True)
class STStorageAdditionalConstraint:
    """Short-term storage additional constraint.

    Attributes:
        id: ID of the additional constraint.
        name: Name of the additional constraint.
        variable: Variable considered for the constraint
            (`WITHDRAWAL`, `INJECTION` or `NETTING`).
        operator: Mathematical operator defining the constraint
            (`LESS`, `GREATER` or `EQUAL`).
        occurrences: List of list of hours where the constraint is applied.
        enabled: Whether the constraint is considered.
    """

    id: str = field(init=False)
    name: str
    variable: AdditionalConstraintVariable = AdditionalConstraintVariable.NETTING
    operator: AdditionalConstraintOperator = AdditionalConstraintOperator.LESS
    occurrences: list[Occurrence] = field(default_factory=list)
    enabled: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", transform_name_to_id(self.name))


@dataclass(frozen=True)
class STStorageAdditionalConstraintUpdate:
    """Short-term storage additional constraint update.

    See the class [`STStorageAdditionalConstraint`][antares.craft.model.st_storage.STStorageAdditionalConstraint]
    for more details on the parameters.
    """

    variable: Optional[AdditionalConstraintVariable] = None
    operator: Optional[AdditionalConstraintOperator] = None
    occurrences: Optional[list[Occurrence]] = None
    enabled: Optional[bool] = None


class STStorage:
    """Short-term storage object of modelling.

    This object allows to represent the management of any short-term storage with the following main characteristics :

    - Storages managed on cycles that are sub-multiples of the Antares optimization window (week or day).
        By cycle we mean that at the end of the cycle the stock must return to the level at the start of the cycle
    - Rule curves that frame the admissible levels hour by hour - the authorized range is a subset of the 0-100 range hourly.
    - PMAX chronicles for storage and destocking.
    - Natural inflows (case of open cycle Pump-Storage Plants).
    """

    def __init__(
        self,
        storage_service: BaseShortTermStorageService,
        area_id: str,
        name: str,
        properties: Optional[STStorageProperties] = None,
        constraints: Optional[dict[str, STStorageAdditionalConstraint]] = None,
    ):
        self._area_id: str = area_id
        self._storage_service: BaseShortTermStorageService = storage_service
        self._name: str = name
        self._id: str = transform_name_to_id(name)
        self._properties: STStorageProperties = properties or STStorageProperties()
        self._constraints = constraints or {}

    @property
    def area_id(self) -> str:
        """Area to which the short-term storage belongs to."""
        return self._area_id

    @property
    def name(self) -> str:
        """Name of the short-term storage."""
        return self._name

    @property
    def id(self) -> str:
        """ID of the short-term storage."""
        return self._id

    @property
    def properties(self) -> STStorageProperties:
        """Properties of the short-term storage."""
        return self._properties

    def get_constraints(self) -> MappingProxyType[str, STStorageAdditionalConstraint]:
        """Get the associated constraints.

        Returns:
            A mapping of the additional constraint ID and the object `STStorageAdditionalConstraint`.
        """
        return MappingProxyType(self._constraints)

    def update_properties(self, properties: STStoragePropertiesUpdate) -> STStorageProperties:
        """Update short-term storage properties.

        Args:
            properties: The properties to update.

        Returns:
            The updated properties.
        """
        new_properties = self._storage_service.update_st_storages_properties({self: properties})
        self._properties = new_properties[self]
        return self._properties

    def get_pmax_injection(self) -> pd.DataFrame:
        """Get the maximum injection power time series.

        Returns:
            The maximum injection power dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.PMAX_INJECTION)

    def get_pmax_withdrawal(self) -> pd.DataFrame:
        """Get the maximum withdrawal power time series.

        Returns:
            The maximum withdrawal power dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.PMAX_WITHDRAWAL)

    def get_lower_rule_curve(self) -> pd.DataFrame:
        """Get the lower rule curve time series.

        Returns:
            The lower rule curve dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.LOWER_CURVE_RULE)

    def get_upper_rule_curve(self) -> pd.DataFrame:
        """Get the upper rule curve time series.

        Returns:
            The upper rule curve dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.UPPER_RULE_CURVE)

    def get_storage_inflows(self) -> pd.DataFrame:
        """Get the natural inflow time series.

        Returns:
            The natural inflow dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.INFLOWS)

    def get_cost_injection(self) -> pd.DataFrame:
        """Get the injection cost time series.

        Returns:
            The injection cost dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.COST_INJECTION)

    def get_cost_withdrawal(self) -> pd.DataFrame:
        """Get the withdrawal cost time series.

        Returns:
            The withdrawal cost dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.COST_WITHDRAWAL)

    def get_cost_level(self) -> pd.DataFrame:
        """Get the level cost time series.

        Returns:
            The level cost dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.COST_LEVEL)

    def get_cost_variation_injection(self) -> pd.DataFrame:
        """Get the variation injection cost time series.

        Returns:
            The variation injection cost dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.COST_VARIATION_INJECTION)

    def get_cost_variation_withdrawal(self) -> pd.DataFrame:
        """Get the variation withdrawal cost time series.

        Returns:
            The variation withdrawal cost dataframe.
        """
        return self._storage_service.get_storage_matrix(self, STStorageMatrixName.COST_VARIATION_WITHDRAWAL)

    def update_pmax_injection(self, p_max_injection_matrix: pd.DataFrame) -> None:
        """Update the maximum injection power time series.

        Args:
            p_max_injection_matrix: The new maximum injection power dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.PMAX_INJECTION, p_max_injection_matrix)

    def set_pmax_withdrawal(self, p_max_withdrawal_matrix: pd.DataFrame) -> None:
        """Set the maximum withdrawal power time series.

        Args:
            p_max_withdrawal_matrix: The new maximum injection power dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.PMAX_WITHDRAWAL, p_max_withdrawal_matrix)

    def set_lower_rule_curve(self, lower_rule_curve_matrix: pd.DataFrame) -> None:
        """Set the lower rule curve time series.

        Args:
            lower_rule_curve_matrix: The new lower rule curve dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.LOWER_CURVE_RULE, lower_rule_curve_matrix)

    def set_upper_rule_curve(self, upper_rule_curve_matrix: pd.DataFrame) -> None:
        """Set the upper rule curve time series.

        Args:
            upper_rule_curve_matrix: The new upper rule curve dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.UPPER_RULE_CURVE, upper_rule_curve_matrix)

    def set_storage_inflows(self, inflows_matrix: pd.DataFrame) -> None:
        """Set storage inflows time series.

        Args:
            inflows_matrix: The new storage inflows dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.INFLOWS, inflows_matrix)

    def set_cost_injection(self, cost_injection_matrix: pd.DataFrame) -> None:
        """Set cost injection time series.

        Args:
            cost_injection_matrix: The new cost injection dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.COST_INJECTION, cost_injection_matrix)

    def set_cost_withdrawal(self, cost_withdrawal_matrix: pd.DataFrame) -> None:
        """Set cost withdrawal time series.

        Args:
            cost_withdrawal_matrix: The new cost withdrawal dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.COST_WITHDRAWAL, cost_withdrawal_matrix)

    def set_cost_level(self, cost_level_matrix: pd.DataFrame) -> None:
        """Set cost level time series.

        Args:
            cost_level_matrix: The new cost level dataframe.
        """
        self._storage_service.set_storage_matrix(self, STStorageMatrixName.COST_LEVEL, cost_level_matrix)

    def set_cost_variation_injection(self, cost_variation_injection_matrix: pd.DataFrame) -> None:
        """Set cost of variation injection time series.

        Args:
            cost_variation_injection_matrix: The new cost of variation injection dataframe.
        """
        self._storage_service.set_storage_matrix(
            self, STStorageMatrixName.COST_VARIATION_INJECTION, cost_variation_injection_matrix
        )

    def set_cost_variation_withdrawal(self, cost_variation_withdrawal_matrix: pd.DataFrame) -> None:
        """Set cost of variation withdrawal time series.

        Args:
            cost_variation_withdrawal_matrix: The new cost of variation withdrawal dataframe.
        """
        self._storage_service.set_storage_matrix(
            self, STStorageMatrixName.COST_VARIATION_WITHDRAWAL, cost_variation_withdrawal_matrix
        )

    def create_constraints(self, constraints: list[STStorageAdditionalConstraint]) -> None:
        """Create a new additional constraints.

        Args:
            constraints: The list of new additional constraints.
        """
        new_constraints = self._storage_service.create_constraints(self._area_id, self._id, constraints)
        for constraint in new_constraints:
            self._constraints[constraint.id] = constraint

    def update_constraint(
        self, constraint_id: str, constraint: STStorageAdditionalConstraintUpdate
    ) -> STStorageAdditionalConstraint:
        """Update an additional constraint.

        Args:
            constraint_id: The constraint ID.
            constraint: The new constraint update.

        Returns:
            The updated constraint.
        """
        updated_constraints = self._storage_service.update_st_storages_constraints({self: {constraint_id: constraint}})
        updated_constraint = updated_constraints[self.area_id][self.id][constraint_id]
        self._constraints[constraint_id] = updated_constraint
        return updated_constraint

    def delete_constraints(self, constraint_ids: list[str]) -> None:
        """Delete additional constraints.

        Args:
            constraint_ids: The list of the constraint IDs to delete.
        """
        self._storage_service.delete_constraints(self._area_id, self._id, constraint_ids)
        for ids in constraint_ids:
            del self._constraints[ids]

    def get_constraint_term(self, constraint_id: str) -> pd.DataFrame:
        """Get constraint term.

        Args:
            constraint_id: The constraint ID.

        Returns:
            The constraint term dataframe.
        """
        return self._storage_service.get_constraint_term(self._area_id, self._id, constraint_id)

    def set_constraint_term(self, constraint_id: str, matrix: pd.DataFrame) -> None:
        """Set constraint term.

        Args:
            constraint_id: The constraint ID.
            matrix: The new constraint dataframe.
        """
        self._storage_service.set_constraint_term(self._area_id, self._id, constraint_id, matrix)
