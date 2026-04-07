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
from io import StringIO
from pathlib import Path
from typing import Any

import pandas as pd

from antares.craft import (
    XpansionCandidate,
    XpansionCandidateUpdate,
    XpansionConstraint,
    XpansionConstraintUpdate,
    XpansionSensitivity,
    XpansionSensitivityUpdate,
    XpansionSettings,
    XpansionSettingsUpdate,
)
from antares.craft.model.output import Frequency
from antares.craft.service.local_services.services.output.date_serializer import FactoryDateSerializer, rename_unnamed


def read_output_matrix(data: Path | StringIO, frequency: Frequency) -> pd.DataFrame:
    df = pd.read_csv(data, sep="\t", skiprows=4, header=[0, 1, 2], na_values="N/A", float_precision="legacy")

    date_serializer = FactoryDateSerializer.create(frequency.value, "")
    _, body = date_serializer.extract_date(df)
    rename_unnamed(body)

    return body.astype(float)


def check_field_is_not_null(data: Any) -> Any:
    assert data is not None
    return data


def update_constraint(
    constraint: XpansionConstraint, constraint_update: XpansionConstraintUpdate
) -> XpansionConstraint:
    constraint_dict = asdict(constraint)
    update_dict = {k: v for k, v in asdict(constraint_update).items() if v is not None}

    constraint_dict["candidates_coefficients"].update(update_dict.pop("candidates_coefficients", {}))
    constraint_dict.update(update_dict)

    return XpansionConstraint(**constraint_dict)


def update_xpansion_settings(settings: XpansionSettings, settings_update: XpansionSettingsUpdate) -> XpansionSettings:
    settings_dict = asdict(settings)
    update_dict = {k: v for k, v in asdict(settings_update).items() if v is not None}
    settings_dict.update(update_dict)

    return XpansionSettings(**settings_dict)


def update_candidate(candidate: XpansionCandidate, candidate_update: XpansionCandidateUpdate) -> XpansionCandidate:
    candidate_dict = asdict(candidate)
    candidate_dict.update({k: v for k, v in asdict(candidate_update).items() if v is not None})
    return XpansionCandidate(**candidate_dict)


def update_sensitivity(
    sensitivity: XpansionSensitivity, sensitivity_update: XpansionSensitivityUpdate
) -> XpansionSensitivity:
    sensitivity_dict = asdict(sensitivity)
    update_dict = {k: v for k, v in asdict(sensitivity_update).items() if v is not None}
    sensitivity_dict.update(update_dict)

    return XpansionSensitivity(**sensitivity_dict)
