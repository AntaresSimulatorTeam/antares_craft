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

from antares.craft.model.settings.adequacy_patch import AdequacyPatchParameters
from antares.craft.model.settings.advanced_parameters import AdvancedParameters, SeedParameters
from antares.craft.model.settings.general import GeneralParameters
from antares.craft.model.settings.optimization import OptimizationParameters
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters


@dataclass
class StudySettings:
    general_parameters: Optional[GeneralParameters] = None
    optimization_parameters: Optional[OptimizationParameters] = None
    advanced_parameters: Optional[AdvancedParameters] = None
    seed_parameters: Optional[SeedParameters] = None
    adequacy_patch_parameters: Optional[AdequacyPatchParameters] = None
    playlist_parameters: Optional[PlaylistParameters] = None
    thematic_trimming_parameters: Optional[ThematicTrimmingParameters] = None
