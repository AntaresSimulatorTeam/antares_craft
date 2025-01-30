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
from typing import Optional

from antares.craft.model.settings.adequacy_patch import AdequacyPatchParametersLocal, DefaultAdequacyPatchParameters
from antares.craft.model.settings.advanced_parameters import AdvancedParameters, SeedParameters
from antares.craft.model.settings.general import GeneralParameters
from antares.craft.model.settings.optimization import OptimizationParameters
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.thematic_trimming import (
    DefaultThematicTrimmingParameters,
    ThematicTrimmingParametersLocal,
)
from antares.craft.tools.all_optional_meta import all_optional_model
from antares.craft.tools.ini_tool import get_ini_fields_for_ini
from pydantic import BaseModel, model_serializer


class DefaultStudySettings(BaseModel):
    general_parameters: GeneralParameters = GeneralParameters()
    optimization_parameters: OptimizationParameters = OptimizationParameters()
    advanced_parameters: AdvancedParameters = AdvancedParameters()
    seed_parameters: SeedParameters = SeedParameters()
    adequacy_patch_parameters: DefaultAdequacyPatchParameters = DefaultAdequacyPatchParameters()
    playlist_parameters: Optional[PlaylistParameters] = None
    thematic_trimming_parameters: Optional[DefaultThematicTrimmingParameters] = None


@all_optional_model
class StudySettings(DefaultStudySettings):
    pass


class StudySettingsLocal(DefaultStudySettings):
    general_parameters: GeneralParameters = GeneralParameters()
    optimization_parameters: OptimizationParameters = OptimizationParameters()
    adequacy_patch_parameters: AdequacyPatchParametersLocal = AdequacyPatchParametersLocal()
    advanced_parameters: AdvancedParameters = AdvancedParameters()
    seed_parameters: SeedParameters = SeedParameters()
    thematic_trimming_parameters: Optional[ThematicTrimmingParametersLocal] = None

    @model_serializer
    def serialize(self) -> dict:
        output_dict = get_ini_fields_for_ini(self)
        return self._sort_fields_last(output_dict)

    @staticmethod
    def _sort_fields_last(output_dict: dict) -> dict:
        new_general = {key: value for key, value in output_dict["general"].items() if key != "readonly"} | {
            "readonly": output_dict["general"]["readonly"]
        }
        new_output = {key: value for key, value in output_dict["output"].items() if key != "result-format"} | {
            "result-format": output_dict["output"]["result-format"]
        }
        output_dict["general"] = new_general
        output_dict["output"] = new_output
        return output_dict
