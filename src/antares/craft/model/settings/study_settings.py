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
from dataclasses import asdict, dataclass, field
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
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters


@dataclass
class StudySettingsUpdate:
    general_parameters: Optional[GeneralParametersUpdate] = None
    optimization_parameters: Optional[OptimizationParametersUpdate] = None
    advanced_parameters: Optional[AdvancedParametersUpdate] = None
    seed_parameters: Optional[SeedParametersUpdate] = None
    adequacy_patch_parameters: Optional[AdequacyPatchParametersUpdate] = None


@dataclass
class StudySettings:
    general_parameters: GeneralParameters = field(default_factory=GeneralParameters)
    optimization_parameters: OptimizationParameters = field(default_factory=OptimizationParameters)
    advanced_parameters: AdvancedParameters = field(default_factory=AdvancedParameters)
    seed_parameters: SeedParameters = field(default_factory=SeedParameters)
    adequacy_patch_parameters: AdequacyPatchParameters = field(default_factory=AdequacyPatchParameters)
    thematic_trimming_parameters: ThematicTrimmingParameters = field(default_factory=ThematicTrimmingParameters)
    playlist_parameters: dict[int, PlaylistParameters] = field(default_factory=dict)

    def from_update_settings(self, update_settings: StudySettingsUpdate) -> "StudySettings":
        current_settings = asdict(self)
        for key, values in asdict(update_settings).items():
            if values is not None:
                for inner_key, inner_value in values.items():
                    if inner_value is not None:
                        current_settings[key][inner_key] = inner_value

        general_parameters = GeneralParameters(**current_settings["general_parameters"])
        optimization_parameters = OptimizationParameters(**current_settings["optimization_parameters"])
        advanced_parameters = AdvancedParameters(**current_settings["advanced_parameters"])
        seed_parameters = SeedParameters(**current_settings["seed_parameters"])
        adequacy_patch_parameters = AdequacyPatchParameters(**current_settings["adequacy_patch_parameters"])
        thematic_trimming_parameters = ThematicTrimmingParameters(**current_settings["thematic_trimming_parameters"])
        playlist_parameters: dict[int, PlaylistParameters] = {}
        for year in current_settings["playlist_parameters"]:
            playlist_parameters[year] = PlaylistParameters(**current_settings["playlist_parameters"][year])

        return StudySettings(
            general_parameters,
            optimization_parameters,
            advanced_parameters,
            seed_parameters,
            adequacy_patch_parameters,
            thematic_trimming_parameters,
            playlist_parameters,
        )

    def to_update_settings(self) -> StudySettingsUpdate:
        current_settings = asdict(self)
        general_parameters = GeneralParametersUpdate(**current_settings["general_parameters"])
        optimization_parameters = OptimizationParametersUpdate(**current_settings["optimization_parameters"])
        advanced_parameters = AdvancedParametersUpdate(**current_settings["advanced_parameters"])
        seed_parameters = SeedParametersUpdate(**current_settings["seed_parameters"])
        adequacy_patch_parameters = AdequacyPatchParametersUpdate(**current_settings["adequacy_patch_parameters"])

        return StudySettingsUpdate(
            general_parameters, optimization_parameters, advanced_parameters, seed_parameters, adequacy_patch_parameters
        )
