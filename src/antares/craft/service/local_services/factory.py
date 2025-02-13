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
import logging
import os
import time
from pathlib import Path

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.study import Study
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseBindingConstraintService,
    BaseHydroService,
    BaseLinkService,
    BaseOutputService,
    BaseRenewableService,
    BaseRunService,
    BaseShortTermStorageService,
    BaseStudyService,
    BaseStudySettingsService,
    BaseThermalService,
)
from antares.craft.service.local_services.area_local import AreaLocalService
from antares.craft.service.local_services.binding_constraint_local import BindingConstraintLocalService
from antares.craft.service.local_services.link_local import LinkLocalService
from antares.craft.service.local_services.services.hydro import HydroLocalService
from antares.craft.service.local_services.services.output import OutputLocalService
from antares.craft.service.local_services.services.renewable import RenewableLocalService
from antares.craft.service.local_services.services.run import RunLocalService
from antares.craft.service.local_services.services.settings import StudySettingsLocalService, edit_study_settings
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.service.local_services.study_local import StudyLocalService
from antares.craft.service.service_factory import ServiceFactory
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


class LocalServiceFactory(ServiceFactory):
    def __init__(self, config: LocalConfiguration, study_id: str = "", study_name: str = ""):
        self.config = config
        self.study_id = study_id
        self.study_name = study_name

    @override
    def create_area_service(self) -> BaseAreaService:
        # TODO: we should not have multiple instances of those services
        storage_service = ShortTermStorageLocalService(self.config, self.study_name)
        thermal_service = ThermalLocalService(self.config, self.study_name)
        renewable_service = RenewableLocalService(self.config, self.study_name)
        hydro_service = HydroLocalService(self.config, self.study_name)
        area_service = AreaLocalService(
            self.config, self.study_name, storage_service, thermal_service, renewable_service, hydro_service
        )
        return area_service

    @override
    def create_link_service(self) -> BaseLinkService:
        return LinkLocalService(self.config, self.study_name)

    @override
    def create_thermal_service(self) -> BaseThermalService:
        return ThermalLocalService(self.config, self.study_name)

    @override
    def create_binding_constraints_service(self) -> BaseBindingConstraintService:
        return BindingConstraintLocalService(self.config, self.study_name)

    @override
    def create_study_service(self) -> BaseStudyService:
        output_service = self.create_output_service()
        study_service = StudyLocalService(self.config, self.study_name, output_service)
        return study_service

    @override
    def create_renewable_service(self) -> BaseRenewableService:
        return RenewableLocalService(self.config, self.study_name)

    @override
    def create_st_storage_service(self) -> BaseShortTermStorageService:
        return ShortTermStorageLocalService(self.config, self.study_name)

    @override
    def create_run_service(self) -> BaseRunService:
        return RunLocalService(self.config, self.study_name)

    @override
    def create_output_service(self) -> BaseOutputService:
        return OutputLocalService(self.config, self.study_name)

    @override
    def create_settings_service(self) -> BaseStudySettingsService:
        return StudySettingsLocalService(self.config, self.study_name)

    @override
    def create_hydro_service(self) -> BaseHydroService:
        return HydroLocalService(self.config, self.study_name)



def _create_correlation_ini_files(study_directory: Path) -> None:
    correlation_inis_to_create = [
        getattr(InitializationFilesTypes, field.upper() + "_CORRELATION_INI")
        for field in ["hydro", "load", "solar", "wind"]
    ]

    ini_content = {"general": {"mode": "annual"}, "annual": {}}
    for k in range(12):
        ini_content[str(k)] = {}

    for file_type in correlation_inis_to_create:
        ini_file = IniFile(
            study_directory,
            file_type,
            ini_contents=ini_content,
        )
        ini_file.write_ini_file()



def _verify_study_already_exists(study_directory: Path) -> None:
    if study_directory.exists():
        raise FileExistsError(f"Study {study_directory.name} already exists.")


def _create_directory_structure(study_path: Path) -> None:
    subdirectories = [
        "input/hydro/allocation",
        "input/hydro/common/capacity",
        "input/hydro/series",
        "input/links",
        "input/load/series",
        "input/misc-gen",
        "input/reserves",
        "input/solar/series",
        "input/thermal/clusters",
        "input/thermal/prepro",
        "input/thermal/series",
        "input/wind/series",
        "layers",
        "output",
        "settings/resources",
        "settings/simulations",
        "user",
    ]
    for subdirectory in subdirectories:
        (study_path / subdirectory).mkdir(parents=True, exist_ok=True)

def create_study_local(study_name: str, version: str, parent_directory: Path) -> "Study":
    """
    Create a directory structure for the study with empty files.

    Args:
        study_name: antares study name to be created
        version: antares version for study
        parent_directory: Local directory to store the study in.

    Raises:
        FileExistsError if the study already exists in the given location
    """
    local_config = LocalConfiguration(parent_directory, study_name)

    study_directory = local_config.local_path / study_name

    _verify_study_already_exists(study_directory)

    # Create the directory structure
    _create_directory_structure(study_directory)

    # Create study.antares file with timestamps and study_name
    antares_file_path = os.path.join(study_directory, "study.antares")
    current_time = int(time.time())
    antares_content = f"""[antares]
version = {version}
caption = {study_name}
created = {current_time}
lastsave = {current_time}
author = Unknown
"""
    with open(antares_file_path, "w") as antares_file:
        antares_file.write(antares_content)

    # Create Desktop.ini file
    desktop_ini_path = study_directory / "Desktop.ini"
    desktop_ini_content = f"""[.ShellClassInfo]
IconFile = settings/resources/study.ico
IconIndex = 0
InfoTip = Antares Study {version}: {study_name}
"""
    with open(desktop_ini_path, "w") as desktop_ini_file:
        desktop_ini_file.write(desktop_ini_content)

    # Create various .ini files for the study
    _create_correlation_ini_files(study_directory)

    logging.info(f"Study successfully created: {study_name}")
    study = Study(
        name=study_name,
        version=version,
        service_factory=LocalServiceFactory(config=local_config, study_name=study_name),
        path=study_directory,
    )
    # We need to create the file with default value
    default_settings = StudySettings()
    update_settings = default_settings.to_update_settings()
    edit_study_settings(study_directory, update_settings, True)
    study._settings = default_settings
    return study


def read_study_local(study_directory: Path) -> "Study":
    """
    Read a study structure by returning a study object.
    Args:
        study_directory: antares study path to be read

    Raises:
        FileNotFoundError: If the provided directory does not exist.
    """

    def _directory_not_exists(local_path: Path) -> None:
        if not local_path.is_dir():
            raise FileNotFoundError(f"The path {local_path} doesn't exist or isn't a folder.")

    _directory_not_exists(study_directory)

    study_antares = IniFile(study_directory, InitializationFilesTypes.ANTARES)

    study_params = study_antares.ini_dict["antares"]

    local_config = LocalConfiguration(study_directory.parent, study_directory.name)

    study = Study(
        name=study_params["caption"],
        version=study_params["version"],
        service_factory=LocalServiceFactory(config=local_config, study_name=study_params["caption"]),
        path=study_directory,
    )
    study.read_settings()
    return study