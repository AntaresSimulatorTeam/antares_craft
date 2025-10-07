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
from typing import Any

from pydantic import Field

from antares.craft.model.commons import STUDY_VERSION_9_3
from antares.craft.model.renewable import (
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesUpdate,
    TimeSeriesInterpretation,
)
from antares.craft.service.local_services.models.base_model import LocalBaseModel
from antares.study.version import StudyVersion

RenewablePropertiesType = RenewableClusterProperties | RenewableClusterPropertiesUpdate


class RenewableClusterPropertiesLocal(LocalBaseModel):
    enabled: bool = True
    unit_count: int = Field(default=1, alias="unitcount")
    nominal_capacity: float = Field(default=0, alias="nominalcapacity")
    group: str = RenewableClusterGroup.OTHER1.value
    ts_interpretation: TimeSeriesInterpretation = Field(
        default=TimeSeriesInterpretation.POWER_GENERATION, alias="ts-interpretation"
    )

    @staticmethod
    def from_user_model(user_class: RenewablePropertiesType) -> "RenewableClusterPropertiesLocal":
        user_dict = {k: v for k, v in asdict(user_class).items() if v is not None}
        return RenewableClusterPropertiesLocal.model_validate(user_dict)

    def to_user_model(self) -> RenewableClusterProperties:
        return RenewableClusterProperties(
            enabled=self.enabled,
            unit_count=self.unit_count,
            nominal_capacity=self.nominal_capacity,
            group=self.group,
            ts_interpretation=self.ts_interpretation,
        )


def validate_renewable_against_version(properties: RenewableClusterPropertiesLocal, version: StudyVersion) -> None:
    if version < STUDY_VERSION_9_3:
        valid_values = [e.value for e in RenewableClusterGroup] + [None]
        if properties.group.lower() not in valid_values:
            raise ValueError(f"Before v9.3, group has to be a valid value : {valid_values}")
        properties.group = properties.group.lower()


def parse_renewable_cluster_local(study_version: StudyVersion, data: Any) -> RenewableClusterProperties:
    local_properties = RenewableClusterPropertiesLocal.model_validate(data)
    validate_renewable_against_version(local_properties, study_version)
    return local_properties.to_user_model()


def serialize_renewable_cluster_local(
    study_version: StudyVersion, renewable: RenewablePropertiesType
) -> dict[str, Any]:
    local_properties = RenewableClusterPropertiesLocal.from_user_model(renewable)
    validate_renewable_against_version(local_properties, study_version)
    return local_properties.model_dump(mode="json", by_alias=True, exclude_none=True, exclude_unset=True)
