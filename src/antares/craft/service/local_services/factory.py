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
from typing import Optional, cast

from antares.craft import BuildingMode, PlaylistParameters
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.binding_constraint import BindingConstraint, ConstraintTerm, ConstraintTermData
from antares.craft.model.link import Link
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.study import Study
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.base_services import StudyServices
from antares.craft.service.local_services.models.binding_constraint import BindingConstraintPropertiesLocal
from antares.craft.service.local_services.models.link import LinkPropertiesAndUiLocal
from antares.craft.service.local_services.models.settings.adequacy_patch import parse_adequacy_parameters_local
from antares.craft.service.local_services.models.settings.advanced_parameters import (
    parse_advanced_and_seed_parameters_local,
)
from antares.craft.service.local_services.models.settings.general import GeneralParametersLocal
from antares.craft.service.local_services.models.settings.optimization import OptimizationParametersLocal
from antares.craft.service.local_services.models.settings.playlist_parameters import PlaylistParametersLocal
from antares.craft.service.local_services.models.settings.thematic_trimming import parse_thematic_trimming_local
from antares.craft.service.local_services.models.xpansion import parse_xpansion_candidate_local
from antares.craft.service.local_services.services.area import AreaLocalService
from antares.craft.service.local_services.services.binding_constraint import BindingConstraintLocalService
from antares.craft.service.local_services.services.hydro import HydroLocalService
from antares.craft.service.local_services.services.link import LinkLocalService
from antares.craft.service.local_services.services.output.output import OutputLocalService
from antares.craft.service.local_services.services.renewable import RenewableLocalService
from antares.craft.service.local_services.services.run import RunLocalService
from antares.craft.service.local_services.services.settings import (
    StudySettingsLocalService,
    edit_study_settings,
    read_ini_settings,
)
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.study import StudyLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.service.local_services.services.xpansion import XpansionLocalService
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
    xpansion_service = XpansionLocalService(config, study_name)
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
        xpansion_service=xpansion_service,
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
    local_services = create_local_services(
        config=local_config,
        study_name=study_params["caption"],
        study_version=version,
    )

    study = Study(
        name=study_params["caption"],
        version=f"{version:2d}",
        services=local_services,
        path=study_directory,
        solver_path=solver_path,
    )

    study._settings = _read_settings(version, study_directory)
    study._read_outputs()

    xp_service = cast(XpansionLocalService, local_services.xpansion_service)
    study._xpansion_configuration = _read_xpansion_configuration(xp_service)

    study._read_areas()

    link_service = cast(LinkLocalService, local_services.link_service)
    study._links = _read_links(link_service)

    bc_service = cast(BindingConstraintLocalService, local_services.bc_service)
    study._binding_constraints = _read_binding_constraints(bc_service)

    return study


def _read_settings(study_version: StudyVersion, study_directory: Path) -> StudySettings:
    ini_content = read_ini_settings(study_directory)

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


def _read_xpansion_configuration(xpansion_service: XpansionLocalService) -> XpansionConfiguration | None:
    if not xpansion_service.xpansion_path.exists():
        return None
    # Settings
    settings = xpansion_service.read_settings()
    # Candidates
    candidates = {}
    ini_candidates = xpansion_service.read_candidates()
    for values in ini_candidates.values():
        cdt = parse_xpansion_candidate_local(values)
        candidates[cdt.name] = cdt
    # Constraints
    constraints = {}
    file_name = settings.additional_constraints
    if file_name:
        constraints = xpansion_service.read_constraints(file_name)
    # Sensitivity
    sensitivity = xpansion_service.read_sensitivity()
    return XpansionConfiguration(
        xpansion_service, settings=settings, candidates=candidates, constraints=constraints, sensitivity=sensitivity
    )


def _read_binding_constraints(bc_service: BindingConstraintLocalService) -> dict[str, BindingConstraint]:
    constraints: dict[str, BindingConstraint] = {}
    current_ini_content = bc_service.read_ini()
    for constraint in current_ini_content.values():
        name = constraint.pop("name")
        del constraint["id"]

        # Separate properties from terms
        properties_fields = BindingConstraintPropertiesLocal().model_dump(by_alias=True)  # type: ignore
        terms_dict = {}
        local_properties_dict = {}
        for k, v in constraint.items():
            if k in properties_fields:
                local_properties_dict[k] = v
            else:
                terms_dict[k] = v

        # Build properties
        local_properties = BindingConstraintPropertiesLocal.model_validate(local_properties_dict)
        properties = local_properties.to_user_model()

        # Build terms
        terms = []
        for key, value in terms_dict.items():
            term_data = ConstraintTermData.from_ini(key)
            if "%" in str(value):
                weight, offset = value.split("%")
            else:
                weight = value
                offset = 0
            term = ConstraintTerm(weight=float(weight), offset=int(offset), data=term_data)
            terms.append(term)

        bc = BindingConstraint(name=name, binding_constraint_service=bc_service, properties=properties, terms=terms)
        constraints[bc.id] = bc

    return constraints


def _read_links(link_service: LinkLocalService) -> dict[str, Link]:
    link_path = link_service.config.study_path / "input" / "links"

    all_links: dict[str, Link] = {}

    for element in link_path.iterdir():
        area_from = element.name
        links_dict = link_service.read_ini(area_from)
        for area_to, values in links_dict.items():
            local_model = LinkPropertiesAndUiLocal.model_validate(values)
            properties = local_model.to_properties_user_model()
            ui = local_model.to_ui_user_model()
            link = Link(area_from=area_from, area_to=area_to, link_service=link_service, properties=properties, ui=ui)
            all_links[link.id] = link

    return all_links
