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
import getpass

from pathlib import Path
from typing import Optional

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.study import Study
from antares.craft.service.base_services import StudyServices
from antares.craft.service.local_services.models.settings.adequacy_patch import parse_adequacy_parameters_local
from antares.craft.service.local_services.models.settings.advanced_parameters import (
    parse_advanced_and_seed_parameters_local,
)
from antares.craft.service.local_services.models.settings.thematic_trimming import parse_thematic_trimming_local
from antares.craft.service.local_services.services.area import AreaLocalService
from antares.craft.service.local_services.services.binding_constraint import BindingConstraintLocalService
from antares.craft.service.local_services.services.hydro import HydroLocalService
from antares.craft.service.local_services.services.link import LinkLocalService
from antares.craft.service.local_services.services.output.output import OutputLocalService
from antares.craft.service.local_services.services.renewable import RenewableLocalService
from antares.craft.service.local_services.services.run import RunLocalService
from antares.craft.service.local_services.services.settings import StudySettingsLocalService, edit_study_settings
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.study import StudyLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp


def create_local_services(config: LocalConfiguration, study_name: str, study_version: StudyVersion) -> StudyServices:
    short_term_storage_service = ShortTermStorageLocalService(config, study_name, study_version)
    thermal_service = ThermalLocalService(config, study_name)
    renewable_service = RenewableLocalService(config, study_name)
    hydro_service = HydroLocalService(config, study_name, study_version)
    bc_service = BindingConstraintLocalService(config, study_name)
    area_service = AreaLocalService(
        config,
        study_name,
        study_version,
        short_term_storage_service,
        thermal_service,
        renewable_service,
        hydro_service,
        bc_service,
    )
    link_service = LinkLocalService(config, study_name)
    output_service = OutputLocalService(config, study_name)
    study_service = StudyLocalService(config, study_name, output_service)
    run_service = RunLocalService(config, study_name)
    settings_service = StudySettingsLocalService(config, study_name, study_version)
    short_term_storage_service = ShortTermStorageLocalService(config, study_name, study_version)
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


def _get_current_os_user() -> str:
    try:
        return getpass.getuser()
    except ModuleNotFoundError:  # Can happen on Windows as the `pwd` module only exists on Unix
        return "Unknown"


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

    study_directory = parent_directory / study_name

    study_version = StudyVersion.parse(version)
    app = CreateApp(study_dir=study_directory, caption=study_name, version=study_version, author=_get_current_os_user())
    app()

    study = Study(
        name=study_name,
        version=version,
        services=create_local_services(config=local_config, study_name=study_name, study_version=study_version),
        path=study_directory,
        solver_path=solver_path,
    )
    # We need to create the file with default values
    default_settings = StudySettings()
    update_settings = default_settings.to_update_settings()
    edit_study_settings(study_directory, update_settings, True, study_version)
    # Initialize settings with the default values
    study._settings.thematic_trimming_parameters = parse_thematic_trimming_local(study_version, {})
    advanced_parameters, seed_parameters = parse_advanced_and_seed_parameters_local(study_version, {})
    study._settings.advanced_parameters = advanced_parameters
    study._settings.seed_parameters = seed_parameters
    study._settings.adequacy_patch_parameters = parse_adequacy_parameters_local(study_version, {})

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

    if not study_directory.is_dir():
        raise FileNotFoundError(f"The given path {study_directory} doesn't exist or isn't a folder.")

    study_antares_path = study_directory / "study.antares"
    study_params = IniReader().read(study_antares_path)["antares"]

    local_config = LocalConfiguration(study_directory.parent, study_directory.name)

    version = StudyVersion.parse(str(study_params["version"]))
    study = Study(
        name=study_params["caption"],
        version=f"{version:2d}",
        services=create_local_services(
            config=local_config,
            study_name=study_params["caption"],
            study_version=version,
        ),
        path=study_directory,
        solver_path=solver_path,
    )
    study._read_settings()
    study._read_areas()
    study._read_links()
    study._read_binding_constraints()
    study._read_outputs()

    return study
