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
import io

from dataclasses import asdict
from typing import Annotated, Any, TypeAlias

from pydantic import BeforeValidator, Field, PlainSerializer

from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import ConstraintSign, XpansionConstraint, XpansionConstraintUpdate
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import (
    Master,
    UcType,
    XpansionSettings,
    XpansionSolver,
)
from antares.craft.service.api_services.models.base_model import APIBaseModel
from antares.craft.tools.alias_generators import to_kebab
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.serde_local.ini_reader import IniReader


@all_optional_model
class XpansionSensitivityAPI(APIBaseModel):
    epsilon: float
    projection: list[str]
    capex: bool


@all_optional_model
class XpansionSettingsAPI(APIBaseModel, alias_generator=None):
    # Due to AntaresWeb legacy Xpansion endpoints, we must not use camel case aliases.
    master: Master
    uc_type: UcType
    optimality_gap: float
    relative_gap: float
    relaxed_optimality_gap: float
    max_iteration: int
    solver: XpansionSolver
    log_level: int
    separation_parameter: float
    batch_size: int
    yearly_weights: str = Field(alias="yearly-weights")  # Due to old AntaresWeb endpoint
    additional_constraints: str = Field(alias="additional-constraints")  # Due to old AntaresWeb endpoint
    timelimit: int
    sensitivity_config: XpansionSensitivityAPI

    @staticmethod
    def from_user_model(
        settings_class: XpansionSettings, sensitivity_class: XpansionSensitivity | None
    ) -> "XpansionSettingsAPI":
        settings_dict = asdict(settings_class)
        sensitivity_dict = {"sensitivity_config": asdict(sensitivity_class) if sensitivity_class else {}}
        settings_dict.update(sensitivity_dict)
        return XpansionSettingsAPI.model_validate(settings_dict)

    def to_sensitivity_model(self) -> XpansionSensitivity:
        assert self.sensitivity_config is not None
        return XpansionSensitivity(
            epsilon=self.sensitivity_config.epsilon,
            projection=self.sensitivity_config.projection,
            capex=self.sensitivity_config.capex,
        )

    def to_settings_model(self) -> XpansionSettings:
        return XpansionSettings(
            master=self.master,
            uc_type=self.uc_type,
            optimality_gap=self.optimality_gap,
            relative_gap=self.relative_gap,
            relaxed_optimality_gap=self.relaxed_optimality_gap,
            max_iteration=self.max_iteration,
            solver=self.solver,
            log_level=self.log_level,
            separation_parameter=self.separation_parameter,
            batch_size=self.batch_size,
            yearly_weights=self.yearly_weights or None,  # AntaresWeb endpoint uses empty strings instead of None
            additional_constraints=self.additional_constraints or None,  # Same here
            timelimit=self.timelimit,
        )


def parse_xpansion_settings_api(data: dict[str, Any]) -> tuple[XpansionSettings, XpansionSensitivity]:
    api_model = XpansionSettingsAPI.model_validate(data)
    return api_model.to_settings_model(), api_model.to_sensitivity_model()


def serialize_xpansion_settings_api(
    settings_class: XpansionSettings, sensitivity_class: XpansionSensitivity | None
) -> dict[str, Any]:
    api_model = XpansionSettingsAPI.from_user_model(settings_class, sensitivity_class)
    return api_model.model_dump(mode="json", by_alias=True, exclude_none=True)


######################
# Candidates part
######################


class XpansionLink(APIBaseModel):
    area_from: str
    area_to: str

    def serialize(self) -> str:
        return f"{self.area_from} - {self.area_to}"


def split_areas(x: str) -> dict[str, str]:
    area_list = sorted(x.split(" - "))
    return {"area_from": area_list[0], "area_to": area_list[1]}


# link parsed and serialized as "area1 - area2"
XpansionLinkStr: TypeAlias = Annotated[
    XpansionLink,
    BeforeValidator(lambda x: split_areas(x)),
    PlainSerializer(lambda x: x.serialize()),
]


@all_optional_model
class XpansionCandidateAPI(APIBaseModel, alias_generator=to_kebab):  # Due to old AntaresWeb endpoint
    name: str
    link: XpansionLinkStr
    annual_cost_per_mw: float
    already_installed_capacity: int
    unit_size: float
    max_units: int
    max_investment: float
    direct_link_profile: str
    indirect_link_profile: str
    already_installed_direct_link_profile: str
    already_installed_indirect_link_profile: str

    @staticmethod
    def from_user_model(user_class: XpansionCandidate) -> "XpansionCandidateAPI":
        user_dict = asdict(user_class)
        user_dict["link"] = user_dict.pop("area_from") + " - " + user_dict.pop("area_to")
        return XpansionCandidateAPI.model_validate(user_dict)

    def to_user_model(self) -> XpansionCandidate:
        assert isinstance(self.link, XpansionLink)
        return XpansionCandidate(
            name=self.name,
            area_from=self.link.area_from,
            area_to=self.link.area_to,
            annual_cost_per_mw=self.annual_cost_per_mw,
            already_installed_capacity=self.already_installed_capacity,
            unit_size=self.unit_size,
            max_units=self.max_units,
            max_investment=self.max_investment,
            direct_link_profile=self.direct_link_profile,
            indirect_link_profile=self.indirect_link_profile,
            already_installed_direct_link_profile=self.already_installed_direct_link_profile,
            already_installed_indirect_link_profile=self.already_installed_indirect_link_profile,
        )


def parse_xpansion_candidate_api(data: dict[str, Any]) -> XpansionCandidate:
    return XpansionCandidateAPI.model_validate(data).to_user_model()


def serialize_xpansion_candidate_api(user_class: XpansionCandidate) -> dict[str, Any]:
    api_model = XpansionCandidateAPI.from_user_model(user_class)
    return api_model.model_dump(mode="json", by_alias=True, exclude_none=True)


######################
# Constraints part
######################

XpansionConstraintType = XpansionConstraint | XpansionConstraintUpdate


@all_optional_model
class XpansionConstraintAPI(APIBaseModel):
    name: str
    sign: ConstraintSign
    rhs: float

    @staticmethod
    def from_user_model(user_class: XpansionConstraintType) -> "XpansionConstraintAPI":
        args = {
            "name": user_class.name,
            "sign": user_class.sign,
            "rhs": user_class.right_hand_side,
        }
        if user_class.candidates_coefficients is not None:
            for candidate, coefficient in user_class.candidates_coefficients.items():
                args[candidate] = coefficient
        return XpansionConstraintAPI.model_validate(args)

    def to_user_model(self) -> XpansionConstraint:
        return XpansionConstraint(
            name=self.name,
            sign=self.sign,
            right_hand_side=self.rhs,
            candidates_coefficients=self.model_extra,  # type: ignore
        )


def parse_xpansion_constraint_api(data: dict[str, Any]) -> XpansionConstraint:
    api_model = XpansionConstraintAPI.model_validate(data)
    return api_model.to_user_model()


def parse_xpansion_constraints_api(data: Any) -> dict[str, XpansionConstraint]:
    parsed_content = {}
    data_as_dict = IniReader().read(io.StringIO(data))
    for values in data_as_dict.values():
        constraint = parse_xpansion_constraint_api(values)
        parsed_content[constraint.name] = constraint
    return parsed_content


def serialize_xpansion_constraint_api(constraint: XpansionConstraint) -> dict[str, Any]:
    args = {
        "name": constraint.name,
        "sign": constraint.sign,
        "rhs": constraint.right_hand_side,
    }
    if constraint.candidates_coefficients is not None:
        for candidate, coefficient in constraint.candidates_coefficients.items():
            args[candidate] = coefficient
    return args


def serialize_xpansion_constraints_api(constraints: dict[str, XpansionConstraint]) -> str:
    api_content = ""
    for k, constraint in enumerate(constraints.values()):
        api_constraint = XpansionConstraintAPI.from_user_model(constraint)
        api_content += f"[{k + 1}]\n"
        api_content += "\n".join(f"{key} = {value}" for key, value in api_constraint.model_dump(mode="json").items())
        api_content += "\n"
    return api_content
