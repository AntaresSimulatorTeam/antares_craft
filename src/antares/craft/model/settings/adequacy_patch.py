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
    DENS = "DENS"
    LOAD = "Load"


@dataclass
class AdequacyPatchParameters:
    include_adq_patch: bool
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: bool
    set_to_null_ntc_between_physical_out_for_first_step: bool
    price_taking_order: PriceTakingOrder
    include_hurdle_cost_csr: bool
    check_csr_cost_function: bool
    threshold_initiate_curtailment_sharing_rule: int
    threshold_display_local_matching_rule_violations: int
    threshold_csr_variable_bounds_relaxation: int


@dataclass
class AdequacyPatchParametersUpdate:
    include_adq_patch: Optional[bool] = None
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: Optional[bool] = None
    set_to_null_ntc_between_physical_out_for_first_step: Optional[bool] = None
    price_taking_order: Optional[PriceTakingOrder] = None
    include_hurdle_cost_csr: Optional[bool] = None
    check_csr_cost_function: Optional[bool] = None
    threshold_initiate_curtailment_sharing_rule: Optional[int] = None
    threshold_display_local_matching_rule_violations: Optional[int] = None
    threshold_csr_variable_bounds_relaxation: Optional[int] = None
