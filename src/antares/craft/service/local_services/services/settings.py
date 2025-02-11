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

from pathlib import Path
from typing import Any

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.settings.advanced_parameters import (
    AdvancedParametersUpdate,
    SeedParametersUpdate,
)
from antares.craft.model.settings.general import BuildingMode
from antares.craft.model.settings.playlist_parameters import PlaylistParameters
from antares.craft.model.settings.study_settings import StudySettings, StudySettingsUpdate
from antares.craft.model.settings.thematic_trimming import ThematicTrimmingParameters
from antares.craft.service.base_services import BaseStudySettingsService
from antares.craft.service.local_services.models.settings import (
    AdequacyPatchParametersLocal,
    AdvancedAndSeedParametersLocal,
    AdvancedParametersLocal,
    GeneralParametersLocal,
    OptimizationParametersLocal,
    OtherPreferencesLocal,
    SeedParametersLocal,
)
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from typing_extensions import override


class StudySettingsLocalService(BaseStudySettingsService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    @override
    def edit_study_settings(self, settings: StudySettingsUpdate) -> None:
        edit_study_settings(self.config.study_path, settings, creation=False)

    @override
    def read_study_settings(self) -> StudySettings:
        return read_study_settings(self.config.study_path)


def read_study_settings(study_directory: Path) -> StudySettings:
    general_data_ini = IniFile(study_directory, InitializationFilesTypes.GENERAL)
    ini_content = general_data_ini.ini_dict

    # general
    general_params_ini = {"general": ini_content["general"]}
    if general_params_ini.pop("derated", None):
        general_params_ini["building_mode"] = BuildingMode.DERATED.value
    if general_params_ini.pop("custom-scenario", None):
        general_params_ini["building_mode"] = BuildingMode.CUSTOM.value
    else:
        general_params_ini["building_mode"] = BuildingMode.AUTOMATIC.value

    excluded_keys = GeneralParametersLocal.get_excluded_fields_for_user_class()
    for key in excluded_keys:
        general_params_ini.pop(key, None)

    output_parameters_ini = {"output": ini_content["output"]}
    local_general_ini = general_params_ini | output_parameters_ini
    general_parameters_local = GeneralParametersLocal.model_validate(local_general_ini)
    general_parameters = general_parameters_local.to_user_model()

    # optimization
    optimization_ini = ini_content["optimization"]
    optimization_ini.pop("link-type", None)
    optimization_parameters_local = OptimizationParametersLocal.model_validate(optimization_ini)
    optimization_parameters = optimization_parameters_local.to_user_model()

    # adequacy_patch
    adequacy_ini = ini_content["adequacy patch"]
    adequacy_parameters_local = AdequacyPatchParametersLocal.model_validate(adequacy_ini)
    adequacy_patch_parameters = adequacy_parameters_local.to_user_model()

    # seed and advanced
    seed_local_parameters = SeedParametersLocal.model_validate(ini_content["seeds - Mersenne Twister"])
    advanced_local_parameters = AdvancedParametersLocal.model_validate(ini_content["advanced parameters"])
    other_preferences_local_parameters = OtherPreferencesLocal.model_validate(ini_content["other preferences"])
    args = {
        "other_preferences": other_preferences_local_parameters,
        "seeds": seed_local_parameters,
        "advanced_parameters": advanced_local_parameters,
    }
    seed_and_advanced_local_parameters = AdvancedAndSeedParametersLocal.model_validate(args)
    seed_parameters = seed_and_advanced_local_parameters.to_seed_parameters_model()
    advanced_parameters = seed_and_advanced_local_parameters.to_advanced_parameters_model()

    # playlist
    playlist_parameters: dict[int, PlaylistParameters] = {}
    if "playlist" in ini_content:
        playlist_parameters = {}
        # todo

    # thematic trimming
    thematic_trimming_parameters = ThematicTrimmingParameters()
    if "variables selection" in ini_content:
        thematic_trimming_parameters = ThematicTrimmingParameters()
        # todo

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=playlist_parameters,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )


def edit_study_settings(study_directory: Path, settings: StudySettingsUpdate, creation: bool) -> None:
    general_data_ini = IniFile(study_directory, InitializationFilesTypes.GENERAL)
    update = not creation
    ini_content = {} if creation else general_data_ini.ini_dict

    # general
    if settings.general_parameters:
        general_local_parameters = GeneralParametersLocal.from_user_model(settings.general_parameters)

        json_content = general_local_parameters.model_dump(mode="json", by_alias=True, exclude_unset=update)
        if "general" in json_content and "building_mode" in json_content["general"]:
            general_values = json_content["general"]
            del general_values["building_mode"]
            building_mode = general_local_parameters.general.building_mode
            general_values["derated"] = building_mode == BuildingMode.DERATED
            general_values["custom-scenario"] = building_mode == BuildingMode.CUSTOM

        ini_content.update(json_content)

    # optimization
    if settings.optimization_parameters:
        optimization_local_parameters = OptimizationParametersLocal.from_user_model(settings.optimization_parameters)
        ini_content.update(
            {"optimization": optimization_local_parameters.model_dump(mode="json", by_alias=True, exclude_unset=update)}
        )

    # adequacy_patch
    if settings.adequacy_patch_parameters:
        adequacy_local_parameters = AdequacyPatchParametersLocal.from_user_model(settings.adequacy_patch_parameters)
        ini_content.update(
            {"adequacy patch": adequacy_local_parameters.model_dump(mode="json", by_alias=True, exclude_unset=update)}
        )

    # seed and advanced
    seed_parameters = settings.seed_parameters or SeedParametersUpdate()
    advanced_parameters = settings.advanced_parameters or AdvancedParametersUpdate()
    advanced_parameters_local = AdvancedAndSeedParametersLocal.from_user_model(advanced_parameters, seed_parameters)
    ini_content.update(advanced_parameters_local.model_dump(mode="json", by_alias=True, exclude_unset=update))

    # playlist
    # todo

    # thematic trimming
    # todo

    # writing
    general_data_ini.ini_dict = ini_content
    general_data_ini.write_ini_file()
