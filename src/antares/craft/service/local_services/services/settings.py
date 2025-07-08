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

from typing_extensions import override

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
from antares.craft.service.local_services.models.settings.adequacy_patch import (
    parse_adequacy_parameters_local,
    serialize_adequacy_parameters_local,
)
from antares.craft.service.local_services.models.settings.advanced_parameters import (
    parse_advanced_and_seed_parameters_local,
    serialize_advanced_and_seed_parameters_local,
)
from antares.craft.service.local_services.models.settings.general import GeneralParametersLocal
from antares.craft.service.local_services.models.settings.optimization import OptimizationParametersLocal
from antares.craft.service.local_services.models.settings.playlist_parameters import PlaylistParametersLocal
from antares.craft.service.local_services.models.settings.thematic_trimming import (
    parse_thematic_trimming_local,
    serialize_thematic_trimming_local,
)
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.study.version import StudyVersion

DUPLICATE_KEYS = [
    "playlist_year_weight",
    "playlist_year +",
    "playlist_year -",
    "select_var -",
    "select_var +",
]


class StudySettingsLocalService(BaseStudySettingsService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    @override
    def edit_study_settings(self, settings: StudySettingsUpdate, study_version: StudyVersion) -> None:
        edit_study_settings(self.config.study_path, settings, creation=False, study_version=study_version)

    @override
    def read_study_settings(self) -> StudySettings:
        return read_study_settings(self.config.study_path, self.study_version)

    @override
    def set_playlist(self, new_playlist: dict[int, PlaylistParameters]) -> None:
        ini_content = _read_ini(self.config.study_path)
        nb_years = ini_content["general"]["nbyears"]
        playlist_local_parameters = PlaylistParametersLocal.create(new_playlist, nb_years)
        ini_content["playlist"] = playlist_local_parameters.model_dump(mode="json", by_alias=True, exclude_none=True)
        _save_ini(self.config.study_path, ini_content)

    @override
    def set_thematic_trimming(self, new_thematic_trimming: ThematicTrimmingParameters) -> ThematicTrimmingParameters:
        ini_content = _read_ini(self.config.study_path)
        ini_content["variables selection"] = serialize_thematic_trimming_local(
            self.study_version, new_thematic_trimming
        )
        _save_ini(self.config.study_path, ini_content)
        # We're performing this round-trip to fill default values
        return parse_thematic_trimming_local(self.study_version, ini_content["variables selection"])


def _read_ini(study_directory: Path) -> dict[str, Any]:
    return IniReader(DUPLICATE_KEYS).read(study_directory / "settings" / "generaldata.ini")


def _save_ini(study_directory: Path, content: dict[str, Any]) -> None:
    ini_path = study_directory / "settings" / "generaldata.ini"
    IniWriter(DUPLICATE_KEYS).write(content, ini_path)


def read_study_settings(study_directory: Path, study_version: StudyVersion) -> StudySettings:
    ini_content = _read_ini(study_directory)

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
        general_params_ini["general"].pop(key, None)

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
    adequacy_patch_parameters = parse_adequacy_parameters_local(study_version, ini_content)

    # seed and advanced
    advanced_parameters, seed_parameters = parse_advanced_and_seed_parameters_local(study_version, ini_content)

    # playlist
    playlist_parameters: dict[int, PlaylistParameters] = {}
    if "playlist" in ini_content:
        local_parameters = PlaylistParametersLocal.model_validate(ini_content["playlist"])
        playlist_parameters = local_parameters.to_user_model(general_parameters.nb_years)

    # thematic trimming
    thematic_trimming_parameters = parse_thematic_trimming_local(
        study_version, ini_content.get("variables selection", {})
    )

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=playlist_parameters,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )


def edit_study_settings(
    study_directory: Path, settings: StudySettingsUpdate, creation: bool, study_version: StudyVersion
) -> None:
    if creation:
        _save_ini(study_directory, {})
    update = not creation
    ini_content = _read_ini(study_directory)

    # general
    if settings.general_parameters:
        general_local_parameters = GeneralParametersLocal.from_user_model(settings.general_parameters)
        ini_content = general_local_parameters.to_ini_file(update=update, current_content=ini_content)

    # optimization
    if settings.optimization_parameters:
        optimization_local_parameters = OptimizationParametersLocal.from_user_model(settings.optimization_parameters)
        ini_content = optimization_local_parameters.to_ini_file(update=update, current_content=ini_content)

    # adequacy_patch
    if settings.adequacy_patch_parameters:
        adequacy_local_parameters = serialize_adequacy_parameters_local(
            settings.adequacy_patch_parameters, study_version
        )
        ini_content = adequacy_local_parameters.to_ini_file(update=update, current_content=ini_content)

    # seed and advanced
    seed_parameters = settings.seed_parameters or SeedParametersUpdate()
    advanced_parameters = settings.advanced_parameters or AdvancedParametersUpdate()
    local_parameters = serialize_advanced_and_seed_parameters_local(
        (advanced_parameters, seed_parameters), study_version
    )
    ini_content = local_parameters.to_ini_file(update=update, current_content=ini_content)

    # writing
    _save_ini(study_directory, ini_content)
