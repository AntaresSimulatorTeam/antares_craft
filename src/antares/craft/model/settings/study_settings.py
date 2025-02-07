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
from typing import Optional

from antares.craft.model.settings.adequacy_patch import AdequacyPatchParameters, AdequacyPatchParametersUpdate
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParameters,
    AdvancedParametersUpdate,
    SeedParameters,
    SeedParametersUpdate,
)
from antares.craft.model.settings.general import GeneralParameters, GeneralParametersUpdate
from antares.craft.model.settings.optimization import OptimizationParameters, OptimizationParametersUpdate
from antares.craft.model.settings.playlist_parameters import PlaylistParameters, PlaylistParametersUpdate
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters, ThematicTrimmingParametersUpdate


@dataclass
class StudySettings:
    general_parameters: GeneralParameters
    optimization_parameters: OptimizationParameters
    advanced_parameters: AdvancedParameters
    seed_parameters: SeedParameters
    adequacy_patch_parameters: AdequacyPatchParameters
    playlist_parameters: dict[int, PlaylistParameters]
    thematic_trimming_parameters: ThematicTrimmingParameters


@dataclass
class StudySettingsUpdate:
    general_parameters: Optional[GeneralParametersUpdate] = None
    optimization_parameters: Optional[OptimizationParametersUpdate] = None
    advanced_parameters: Optional[AdvancedParametersUpdate] = None
    seed_parameters: Optional[SeedParametersUpdate] = None
    adequacy_patch_parameters: Optional[AdequacyPatchParametersUpdate] = None
    playlist_parameters: Optional[dict[int, PlaylistParametersUpdate]] = None
    thematic_trimming_parameters: Optional[ThematicTrimmingParametersUpdate] = None
