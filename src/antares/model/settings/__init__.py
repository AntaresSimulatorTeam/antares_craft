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

from typing import Dict, Optional

from pydantic import BaseModel

from antares.model.settings.adequacy_patch import AdequacyPatchProperties
from antares.model.settings.advanced_parameters import AdvancedProperties
from antares.model.settings.general import GeneralProperties
from antares.model.settings.optimization import OptimizationProperties
from antares.model.settings.thematic_trimming import ThematicTrimming
from antares.model.settings.time_series import TimeSeriesProperties


class PlaylistData(BaseModel):
    status: bool
    weight: float


class StudySettings(BaseModel):
    general_properties: Optional[GeneralProperties] = None
    thematic_trimming: Optional[ThematicTrimming] = None
    time_series_properties: Optional[TimeSeriesProperties] = None
    adequacy_patch_properties: Optional[AdequacyPatchProperties] = None
    advanced_properties: Optional[AdvancedProperties] = None
    optimization_properties: Optional[OptimizationProperties] = None
    playlist: Optional[Dict[str, PlaylistData]] = None
