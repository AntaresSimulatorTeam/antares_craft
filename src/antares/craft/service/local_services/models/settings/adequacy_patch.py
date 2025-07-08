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
from dataclasses import asdict
from typing import Any, Optional

from antares.craft.model.settings.adequacy_patch import (
    AdequacyPatchParameters,
    AdequacyPatchParametersUpdate,
    PriceTakingOrder,
)
from antares.craft.model.study import STUDY_VERSION_9_2
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.service.local_services.models.utils import check_min_version, initialize_field_default
from antares.craft.tools.alias_generators import to_kebab
from antares.study.version import StudyVersion

AdequacyPatchParametersType = AdequacyPatchParameters | AdequacyPatchParametersUpdate


class AdequacyPatchParametersLocal(LocalBaseModel, alias_generator=to_kebab):
    include_adq_patch: bool = False
    set_to_null_ntc_from_physical_out_to_physical_in_for_first_step: bool = True
    price_taking_order: PriceTakingOrder = PriceTakingOrder.DENS
    include_hurdle_cost_csr: bool = False
    check_csr_cost_function: bool = False
    threshold_initiate_curtailment_sharing_rule: int = 1
    threshold_display_local_matching_rule_violations: int = 0
    threshold_csr_variable_bounds_relaxation: int = 7
    enable_first_step: bool = False
    # Parameters removed since v9.2
    set_to_null_ntc_between_physical_out_for_first_step: Optional[bool] = None

    @staticmethod
    def get_9_2_removed_fields_and_default_value() -> dict[str, Any]:
        return {"set_to_null_ntc_between_physical_out_for_first_step": True}

    @staticmethod
    def from_user_model(user_class: AdequacyPatchParametersType) -> "AdequacyPatchParametersLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return AdequacyPatchParametersLocal.model_validate(user_dict)

    def to_ini_file(self, update: bool, current_content: dict[str, Any]) -> dict[str, Any]:
        content = self.model_dump(mode="json", by_alias=True, exclude_unset=update, exclude_none=True)
        current_content.setdefault("adequacy patch", {}).update(content)
        return current_content

    def to_user_model(self) -> AdequacyPatchParameters:
        return AdequacyPatchParameters(
            include_adq_patch=self.include_adq_patch,
            set_to_null_ntc_from_physical_out_to_physical_in_for_first_step=self.set_to_null_ntc_from_physical_out_to_physical_in_for_first_step,
            set_to_null_ntc_between_physical_out_for_first_step=self.set_to_null_ntc_between_physical_out_for_first_step,
            price_taking_order=self.price_taking_order,
            include_hurdle_cost_csr=self.include_hurdle_cost_csr,
            check_csr_cost_function=self.check_csr_cost_function,
            threshold_initiate_curtailment_sharing_rule=self.threshold_initiate_curtailment_sharing_rule,
            threshold_display_local_matching_rule_violations=self.threshold_display_local_matching_rule_violations,
            threshold_csr_variable_bounds_relaxation=self.threshold_csr_variable_bounds_relaxation,
        )


def validate_against_version(parameters: AdequacyPatchParametersLocal, version: StudyVersion) -> None:
    if version >= STUDY_VERSION_9_2:
        for field in AdequacyPatchParametersLocal.get_9_2_removed_fields_and_default_value():
            check_min_version(parameters, field, version)


def initialize_with_version(
    parameters: AdequacyPatchParametersLocal, version: StudyVersion
) -> AdequacyPatchParametersLocal:
    if version < STUDY_VERSION_9_2:
        for field, value in AdequacyPatchParametersLocal.get_9_2_removed_fields_and_default_value().items():
            initialize_field_default(parameters, field, value)
    return parameters


def parse_adequacy_parameters_local(study_version: StudyVersion, data: Any) -> AdequacyPatchParameters:
    local_parameters = AdequacyPatchParametersLocal.model_validate(data.get("adequacy patch", {}))
    validate_against_version(local_parameters, study_version)
    initialize_with_version(local_parameters, study_version)
    return local_parameters.to_user_model()


def serialize_adequacy_parameters_local(
    parameters: AdequacyPatchParametersType, study_version: StudyVersion
) -> AdequacyPatchParametersLocal:
    local_parameters = AdequacyPatchParametersLocal.from_user_model(parameters)
    validate_against_version(local_parameters, study_version)
    return local_parameters
