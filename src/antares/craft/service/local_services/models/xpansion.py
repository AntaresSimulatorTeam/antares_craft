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
from typing import Annotated, Any, Optional, TypeAlias

from pydantic import BeforeValidator, Field, PlainSerializer

from antares.craft.model.xpansion.candidate import XpansionCandidate
from antares.craft.model.xpansion.constraint import ConstraintSign, XpansionConstraint
from antares.craft.model.xpansion.sensitivity import XpansionSensitivity
from antares.craft.model.xpansion.settings import (
    Master,
    UcType,
    XpansionSettings,
    XpansionSolver,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.craft.tools.alias_generators import to_kebab


class XpansionSettingsLocal(LocalBaseModel):
    master: Master = Master.INTEGER
    uc_type: UcType = UcType.EXPANSION_FAST
    optimality_gap: float = 1
    relative_gap: float = 1e-6
    relaxed_optimality_gap: float = 1e-5
    max_iteration: int = 1000
    solver: XpansionSolver = XpansionSolver.XPRESS
    log_level: int = 0
    separation_parameter: float = 0.5
    batch_size: int = 96
    yearly_weights: Optional[str] = Field(None, alias="yearly-weights")
    additional_constraints: Optional[str] = Field(None, alias="additional-constraints")
    timelimit: int = int(1e12)

    @staticmethod
    def from_user_model(user_class: XpansionSettings) -> "XpansionSettingsLocal":
        user_dict = asdict(user_class)
        return XpansionSettingsLocal.model_validate(user_dict)

    def to_user_model(self) -> XpansionSettings:
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
            yearly_weights=self.yearly_weights,
            additional_constraints=self.additional_constraints,
            timelimit=self.timelimit,
        )


def parse_xpansion_settings_local(data: Any) -> XpansionSettings:
    local_settings = XpansionSettingsLocal.model_validate(data)
    return local_settings.to_user_model()


def serialize_xpansion_settings_local(settings: XpansionSettings) -> dict[str, Any]:
    local_settings = XpansionSettingsLocal.from_user_model(settings)
    return local_settings.model_dump(mode="json", by_alias=True, exclude_none=True)


######################
# Candidates part
######################


class XpansionLink(LocalBaseModel):
    area_from: str
    area_to: str

    def serialize(self) -> str:
        return f"{self.area_from} - {self.area_to}"


def split_areas(x: str) -> dict[str, str]:
    if " - " not in x:
        raise ValueError(f"The link must be in the format 'area1 - area2'. Currently: {x}")
    area_list = sorted(x.split(" - "))
    return {"area_from": area_list[0], "area_to": area_list[1]}


# link parsed and serialized as "area1 - area2"
XpansionLinkStr: TypeAlias = Annotated[
    XpansionLink,
    BeforeValidator(lambda x: split_areas(x)),
    PlainSerializer(lambda x: x.serialize()),
]


class XpansionCandidateLocal(LocalBaseModel, alias_generator=to_kebab):
    name: str
    link: XpansionLinkStr
    annual_cost_per_mw: float = Field(ge=0)
    unit_size: Optional[float] = Field(default=None, ge=0)
    max_units: Optional[int] = Field(default=None, ge=0)
    max_investment: Optional[float] = Field(default=None, ge=0)
    already_installed_capacity: Optional[int] = Field(default=None, ge=0)
    direct_link_profile: Optional[str] = None
    indirect_link_profile: Optional[str] = None
    already_installed_direct_link_profile: Optional[str] = None
    already_installed_indirect_link_profile: Optional[str] = None

    @staticmethod
    def from_user_model(user_class: XpansionCandidate) -> "XpansionCandidateLocal":
        user_dict = asdict(user_class)
        user_dict["link"] = user_dict.pop("area_from") + " - " + user_dict.pop("area_to")
        return XpansionCandidateLocal.model_validate(user_dict)

    def to_user_model(self) -> XpansionCandidate:
        return XpansionCandidate(
            name=self.name,
            area_from=self.link.area_from,
            area_to=self.link.area_to,
            annual_cost_per_mw=self.annual_cost_per_mw,
            unit_size=self.unit_size,
            max_units=self.max_units,
            max_investment=self.max_investment,
            already_installed_capacity=self.already_installed_capacity,
            direct_link_profile=self.direct_link_profile,
            indirect_link_profile=self.indirect_link_profile,
            already_installed_direct_link_profile=self.already_installed_direct_link_profile,
        )


def parse_xpansion_candidate_local(data: dict[str, Any]) -> XpansionCandidate:
    return XpansionCandidateLocal.model_validate(data).to_user_model()


def serialize_xpansion_candidate_local(user_class: XpansionCandidate) -> dict[str, Any]:
    local_model = XpansionCandidateLocal.from_user_model(user_class)
    return local_model.model_dump(mode="json", by_alias=True, exclude_none=True)


######################
# Constraints part
######################


class XpansionConstraintLocal(LocalBaseModel, extra="allow"):
    name: str
    sign: ConstraintSign
    rhs: float

    @staticmethod
    def from_user_model(user_class: XpansionConstraint) -> "XpansionConstraintLocal":
        user_dict = asdict(user_class)
        user_dict["rhs"] = user_dict.pop("right_hand_side")
        user_dict.update(user_dict.pop("candidates_coefficients"))
        return XpansionConstraintLocal.model_validate(user_dict)

    def to_user_model(self) -> XpansionConstraint:
        return XpansionConstraint(
            name=self.name,
            sign=self.sign,
            right_hand_side=self.rhs,
            candidates_coefficients=self.model_extra,  # type: ignore
        )


def parse_xpansion_constraints_local(data: dict[str, Any]) -> dict[str, XpansionConstraint]:
    parsed_content = {}
    for values in data.values():
        local_model = XpansionConstraintLocal.model_validate(values)
        parsed_content[local_model.name] = local_model.to_user_model()
    return parsed_content


def serialize_xpansion_constraints_local(constraints: dict[str, XpansionConstraint]) -> dict[str, Any]:
    serialized_content = {}
    for k, constraint in enumerate(constraints.values()):
        local_model = XpansionConstraintLocal.from_user_model(constraint)
        serialized_content[str(k + 1)] = local_model.model_dump(mode="json", by_alias=True, exclude_none=True)
    return serialized_content


######################
# Sensitivity part
######################


class XpansionSensitivityLocal(LocalBaseModel):
    epsilon: float = Field(ge=0)
    projection: list[str]
    capex: bool

    @staticmethod
    def from_user_model(user_class: XpansionSensitivity) -> "XpansionSensitivityLocal":
        user_dict = asdict(user_class)
        return XpansionSensitivityLocal.model_validate(user_dict)

    def to_user_model(self) -> XpansionSensitivity:
        return XpansionSensitivity(epsilon=self.epsilon, projection=self.projection, capex=self.capex)


def parse_xpansion_sensitivity_local(data: dict[str, Any]) -> XpansionSensitivity:
    return XpansionSensitivityLocal.model_validate(data).to_user_model()


def serialize_xpansion_sensitivity_local(user_class: XpansionSensitivity) -> dict[str, Any]:
    local_model = XpansionSensitivityLocal.from_user_model(user_class)
    return local_model.model_dump(mode="json", by_alias=True, exclude_none=True)
