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
from typing import Optional

from pydantic import BaseModel
from pydantic.alias_generators import to_camel


class PriceTakingOrder(Enum):
    DENS = "DENS"
    LOAD = "Load"


class AdequacyPatchProperties(BaseModel, alias_generator=to_camel):
    # version 830
    enable_adequacy_patch: Optional[bool] = None
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: Optional[bool] = None
    ntc_between_physical_areas_out_adequacy_patch: Optional[bool] = None
    # version 850
    price_taking_order: Optional[PriceTakingOrder] = None
    include_hurdle_cost_csr: Optional[bool] = None
    check_csr_cost_function: Optional[bool] = None
    threshold_initiate_curtailment_sharing_rule: Optional[int] = None
    threshold_display_local_matching_rule_violations: Optional[int] = None
    threshold_csr_variable_bounds_relaxation: Optional[int] = None
