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

from antares.craft.tools.all_optional_meta import all_optional_model
from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel


class PriceTakingOrder(Enum):
    DENS = "DENS"
    LOAD = "Load"


class DefaultAdequacyPatchParameters(BaseModel, populate_by_name=True, alias_generator=to_camel):
    model_config = ConfigDict(use_enum_values=True)

    # version 830
    enable_adequacy_patch: bool = False
    ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch: bool = True
    ntc_between_physical_areas_out_adequacy_patch: bool = True
    # version 850
    price_taking_order: PriceTakingOrder = Field(default=PriceTakingOrder.DENS, validate_default=True)
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    enable_first_step: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 0
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 3


@all_optional_model
class AdequacyPatchParameters(DefaultAdequacyPatchParameters):
    pass


class AdequacyPatchParametersLocal(DefaultAdequacyPatchParameters):
    @property
    def ini_fields(self) -> dict:
        return {
            "adequacy patch": {
                "include-adq-patch": str(self.enable_adequacy_patch).lower(),
                "set-to-null-ntc-from-physical-out-to-physical-in-for-first-step": str(
                    self.ntc_from_physical_areas_out_to_physical_areas_in_adequacy_patch
                ).lower(),
                "set-to-null-ntc-between-physical-out-for-first-step": str(
                    self.ntc_between_physical_areas_out_adequacy_patch
                ).lower(),
                "enable-first-step": str(self.enable_first_step).lower(),
                "price-taking-order": self.price_taking_order,
                "include-hurdle-cost-csr": str(self.include_hurdle_cost_csr).lower(),
                "check-csr-cost-function": str(self.check_csr_cost_function).lower(),
                "threshold-initiate-curtailment-sharing-rule": f"{self.threshold_initiate_curtailment_sharing_rule:.6f}",
                "threshold-display-local-matching-rule-violations": f"{self.threshold_display_local_matching_rule_violations:.6f}",
                "threshold-csr-variable-bounds-relaxation": f"{self.threshold_csr_variable_bounds_relaxation}",
            }
        }
