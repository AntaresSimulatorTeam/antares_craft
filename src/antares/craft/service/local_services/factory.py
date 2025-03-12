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
from typing import Optional

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.study import Study
from antares.craft.service.base_services import (
    StudyServices,
)
from antares.craft.service.local_services.services.area import AreaLocalService
from antares.craft.service.local_services.services.binding_constraint import BindingConstraintLocalService
from antares.craft.service.local_services.services.hydro import HydroLocalService
from antares.craft.service.local_services.services.link import LinkLocalService
from antares.craft.service.local_services.services.output import OutputLocalService
from antares.craft.service.local_services.services.renewable import RenewableLocalService
from antares.craft.service.local_services.services.run import RunLocalService
from antares.craft.service.local_services.services.settings import StudySettingsLocalService, edit_study_settings
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.study import StudyLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


def create_local_services(config: LocalConfiguration, study_name: str = "") -> StudyServices:
    storage_service = ShortTermStorageLocalService(config, study_name)
    thermal_service = ThermalLocalService(config, study_name)
    renewable_service = RenewableLocalService(config, study_name)
    hydro_service = HydroLocalService(config, study_name)
    area_service = AreaLocalService(
        config, study_name, storage_service, thermal_service, renewable_service, hydro_service
    )
    link_service = LinkLocalService(config, study_name)
    output_service = OutputLocalService(config, study_name)
    study_service = StudyLocalService(config, study_name, output_service)
    bc_service = BindingConstraintLocalService(config, study_name)
    run_service = RunLocalService(config, study_name)
    settings_service = StudySettingsLocalService(config, study_name)
    short_term_storage_service = ShortTermStorageLocalService(config, study_name)
    return StudyServices(
        area_service=area_service,
        bc_service=bc_service,
        run_service=run_service,
        thermal_service=thermal_service,
        hydro_service=hydro_service,
        output_service=output_service,
        study_service=study_service,
        link_service=link_service,
        renewable_service=renewable_service,
        settings_service=settings_service,
        short_term_storage_service=short_term_storage_service,
    )


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


def create_study_local(
    study_name: str, version: str, parent_directory: Path, solver_path: Optional[Path] = None
) -> "Study":
    """
    Create a directory structure for the study with empty files.

    Args:
        study_name: antares study name to be created
        version: antares version for study
        parent_directory: Local directory to store the study in.
        solver_path: antares solver path to use to run simulations

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
        services=create_local_services(config=local_config, study_name=study_name),
        path=study_directory,
        solver_path=solver_path,
    )
    # We need to create the file with default value
    default_settings = StudySettings()
    update_settings = default_settings.to_update_settings()
    edit_study_settings(study_directory, update_settings, True)
    study._settings = default_settings
    return study


def read_study_local(study_directory: Path, solver_path: Optional[Path] = None) -> "Study":
    """
    Read a study structure by returning a study object.
    Args:
        study_directory: antares study path to be read
        solver_path: antares solver path to use to run simulations

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
        services=create_local_services(config=local_config, study_name=study_params["caption"]),
        path=study_directory,
        solver_path=solver_path,
    )
    study._read_settings()
    study._read_areas()
    study._read_links()
    study._read_binding_constraints()
    study._read_outputs()

    return study
