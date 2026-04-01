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


class PriceTakingOrder(Enum):
    """Enumeration of the different price taking order.
    
    Attributes:
        DENS: Domestic Energy Not Served.
        LOAD: Load.
    """
    DENS = "DENS"
    LOAD = "Load"


@dataclass(frozen=True)
class AdequacyPatchParameters:
    """Parameters for the use of adequacy patch.

    Attributes:
        include_adq_patch: Whether to enable the adequacy patch.
        set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: Exclude contribution of flows 
            between physical areas outside and physical areas inside of the adequacy patch domain for DENS reduction
        price_taking_order: Either LOAD or DENS.
        include_hurdle_cost_csr: Whether to include hurdle cost 
        check_csr_cost_function: Whether to include an approximation of redispatching costs 
            (energy transmission, losses, etc.).
        threshold_initiate_curtailment_sharing_rule: Minimum level of the total amount of ENS “inside”
            an area of the adq patch domain in order to activate the CSR
        threshold_display_local_matching_rule_violations: Threshold used to calculate an output indicator (“LMR VIOL.”) 
            counting the number of situations where the application of local matching led to residual energy deviations 
            exceeding this threshold (0: no tolerance).
        threshold_csr_variable_bounds_relaxation: In order to avoid solver issues, 
            lower and upper boundaries of the ENS variable and lower bound of the spillage variable 
            can be relaxed with this parameter.
        set_to_null_ntc_between_physical_out_for_first_step: **Parameter removed since Antares Simulator v9.2, was true in v8.8.**
    """
    include_adq_patch: bool = False
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: bool = True
    price_taking_order: PriceTakingOrder = PriceTakingOrder.DENS
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 1
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 7
    # Parameter removed since v9.2
    set_to_null_ntc_between_physical_out_for_first_step: bool | None = None  # was True in v8.8
    # Parameter introduced in v9.3
    redispatch: bool | None = None


@dataclass
class AdequacyPatchParametersUpdate:
    """A class for updating [`AdequacyPatchParameters`][antares.craft.model.settings.adequacy_patch.AdequacyPatchParameters].
    All fields are optional. If a field is `None`, it will not be updated.
    See `AdequacyPatchParameters` for field descriptions.
    """
    include_adq_patch: Optional[bool] = None
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: Optional[bool] = None
    set_to_null_ntc_between_physical_out_for_first_step: Optional[bool] = None
    price_taking_order: Optional[PriceTakingOrder] = None
    include_hurdle_cost_csr: Optional[bool] = None
    check_csr_cost_function: Optional[bool] = None
    threshold_initiate_curtailment_sharing_rule: Optional[int] = None
    threshold_display_local_matching_rule_violations: Optional[int] = None
    threshold_csr_variable_bounds_relaxation: Optional[int] = None
    redispatch: Optional[bool] = None
