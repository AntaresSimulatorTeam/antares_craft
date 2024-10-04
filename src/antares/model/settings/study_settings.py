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

from typing import Dict

from pydantic import BaseModel

from antares.model.settings.adequacy_patch import DefaultAdequacyPatchProperties
from antares.model.settings.advanced_parameters import AdvancedProperties
from antares.model.settings.general import DefaultGeneralProperties
from antares.model.settings.optimization import OptimizationProperties
from antares.model.settings.thematic_trimming import ThematicTrimming
from antares.model.settings.time_series import TimeSeriesProperties
from antares.tools.all_optional_meta import all_optional_model


class PlaylistData(BaseModel):
    status: bool
    weight: float


class DefaultStudySettings(BaseModel):
    general_properties: DefaultGeneralProperties = DefaultGeneralProperties()
    thematic_trimming: ThematicTrimming = ThematicTrimming()
    # These parameters are listed under the [variables selection] section in the .ini file.
    # They are required if thematic-trimming is set to true.
    # https://antares-simulator.readthedocs.io/en/latest/user-guide/solver/04-parameters/#variables-selection-parameters
    time_series_properties: TimeSeriesProperties = TimeSeriesProperties()
    # These parameters are listed under the [general] section in the .ini file.
    # https://antares-simulator.readthedocs.io/en/latest/user-guide/ts-generator/04-parameters/
    adequacy_patch_properties: DefaultAdequacyPatchProperties = DefaultAdequacyPatchProperties()
    advanced_properties: AdvancedProperties = AdvancedProperties()
    optimization_properties: OptimizationProperties = OptimizationProperties()
    playlist: Dict[str, PlaylistData] = {}


@all_optional_model
class StudySettings(DefaultStudySettings):
    pass


class StudySettingsLocal(DefaultStudySettings):
    pass
