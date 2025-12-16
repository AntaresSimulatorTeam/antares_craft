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
from typing import Any, Optional, cast

from antares.craft import HydroProperties
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.area import Area
from antares.craft.model.commons import STUDY_VERSION_9_2
from antares.craft.model.link import Link
from antares.craft.model.renewable import RenewableCluster
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.st_storage import STStorage
from antares.craft.model.study import Study
from antares.craft.model.thermal import ThermalCluster
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.base_services import StudyServices
from antares.craft.service.local_services.models.area import AreaPropertiesLocal, AreaUiLocal
from antares.craft.service.local_services.models.hydro import parse_hydro_properties_local
from antares.craft.service.local_services.models.link import LinkPropertiesAndUiLocal
from antares.craft.service.local_services.models.renewable import (
    parse_renewable_cluster_local,
)
from antares.craft.service.local_services.models.settings.adequacy_patch import parse_adequacy_parameters_local
from antares.craft.service.local_services.models.settings.advanced_parameters import (
    parse_advanced_and_seed_parameters_local,
)
from antares.craft.service.local_services.models.settings.thematic_trimming import parse_thematic_trimming_local
from antares.craft.service.local_services.models.st_storage import parse_st_storage_local
from antares.craft.service.local_services.models.thermal import (
    parse_thermal_cluster_local,
)
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
    read_study_settings,
)
from antares.craft.service.local_services.services.st_storage import ShortTermStorageLocalService
from antares.craft.service.local_services.services.study import StudyLocalService
from antares.craft.service.local_services.services.thermal import ThermalLocalService
from antares.craft.service.local_services.services.xpansion import XpansionLocalService
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.study.version import StudyVersion
from antares.study.version.create_app import CreateApp


def create_local_services(config: LocalConfiguration, study_name: str, study_version: StudyVersion) -> StudyServices:
    short_term_storage_service = ShortTermStorageLocalService(config, study_name, study_version)
    thermal_service = ThermalLocalService(config, study_name, study_version)
    renewable_service = RenewableLocalService(config, study_name, study_version)
    hydro_service = HydroLocalService(config, study_name, study_version)
    bc_service = BindingConstraintLocalService(config, study_name)
    link_service = LinkLocalService(config, study_name)
    area_service = AreaLocalService(
        config,
        study_name,
        study_version,
        short_term_storage_service,
        thermal_service,
        renewable_service,
        hydro_service,
        bc_service,
        link_service,
    )
    output_service = OutputLocalService(config, study_name)
    study_service = StudyLocalService(config, study_name, output_service)
    run_service = RunLocalService(config, study_name)
    settings_service = StudySettingsLocalService(config, study_name, study_version)
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

    study._settings = read_study_settings(version, study_directory)
    study._read_outputs()

    xp_service = cast(XpansionLocalService, local_services.xpansion_service)
    study._xpansion_configuration = _read_xpansion_configuration(xp_service)

    area_service = cast(AreaLocalService, local_services.area_service)
    study._areas = _read_areas(area_service)

    link_service = cast(LinkLocalService, local_services.link_service)
    study._links = _read_links(link_service)

    bc_service = cast(BindingConstraintLocalService, local_services.bc_service)
    study._binding_constraints = bc_service.read_binding_constraints()

    return study


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


def _read_areas(area_service: AreaLocalService) -> dict[str, Area]:
    areas_path = area_service.config.study_path / "input" / "areas"
    if not areas_path.exists():
        return {}

    # Perf: Read only once the hydro_ini file as it's common to every area
    hydro_service = cast(HydroLocalService, area_service.hydro_service)
    all_hydro_properties = _read_hydro_properties(hydro_service)

    # Read all thermals
    thermal_service = cast(ThermalLocalService, area_service.thermal_service)
    thermals = _read_thermal_clusters(thermal_service)

    # Read all renewables
    renewable_service = cast(RenewableLocalService, area_service.renewable_service)
    renewables = _read_renewables(renewable_service)

    # Read all st_storages
    sts_service = cast(ShortTermStorageLocalService, area_service.storage_service)
    st_storages = _read_st_storages(sts_service)

    # Perf: Read only once the thermal_areas_ini file as it's common to every area
    thermal_area_dict = area_service.read_thermal_areas_ini()

    all_areas: dict[str, Area] = {}
    for element in areas_path.iterdir():
        if element.is_dir():
            area_id = element.name
            optimization_dict = area_service.read_optimization_ini(area_id)
            area_adequacy_dict = area_service.read_adequacy_ini(area_id)
            unserverd_energy_cost = thermal_area_dict.get("unserverdenergycost", {}).get(area_id, 0)
            spilled_energy_cost = thermal_area_dict.get("spilledenergycost", {}).get(area_id, 0)
            local_properties_dict = {
                **optimization_dict,
                **area_adequacy_dict,
                "energy_cost_unsupplied": unserverd_energy_cost,
                "energy_cost_spilled": spilled_energy_cost,
            }
            local_properties = AreaPropertiesLocal.model_validate(local_properties_dict)
            area_properties = local_properties.to_user_model()
            ui_dict = area_service.read_ui_ini(area_id)

            local_ui = AreaUiLocal.model_validate(ui_dict)
            ui_properties = local_ui.to_user_model()

            # Hydro
            inflow_structure = hydro_service.read_inflow_structure_for_one_area(area_id)
            allocation = hydro_service.read_allocation_for_area(area_id)

            area = Area(
                name=area_id,
                area_service=area_service,
                storage_service=area_service.storage_service,
                thermal_service=area_service.thermal_service,
                renewable_service=area_service.renewable_service,
                hydro_service=area_service.hydro_service,
                properties=area_properties,
                ui=ui_properties,
            )
            area.hydro._properties = all_hydro_properties[area.id]
            area.hydro._inflow_structure = inflow_structure
            area.hydro._allocation = allocation
            area._thermals = thermals.get(area.id, {})
            area._renewables = renewables.get(area.id, {})
            area._st_storages = st_storages.get(area.id, {})
            all_areas[area.id] = area

    return all_areas


def _read_hydro_properties(hydro_service: HydroLocalService) -> dict[str, HydroProperties]:
    hydro_properties: dict[str, HydroProperties] = {}

    current_content = hydro_service.read_hydro_ini()

    body_by_area: dict[str, dict[str, Any]] = {}
    for key, value in current_content.items():
        for area_id, data in value.items():
            body_by_area.setdefault(area_id, {})[key] = data
    for area_id, local_properties in body_by_area.items():
        user_properties = parse_hydro_properties_local(hydro_service.study_version, local_properties)
        hydro_properties[area_id] = user_properties

    return hydro_properties


def _read_thermal_clusters(thermal_service: ThermalLocalService) -> dict[str, dict[str, ThermalCluster]]:
    thermals: dict[str, dict[str, ThermalCluster]] = {}
    cluster_path = thermal_service.config.study_path / "input" / "thermal" / "clusters"
    if not cluster_path.exists():
        return {}
    for folder in cluster_path.iterdir():
        if folder.is_dir():
            area_id = folder.name
            thermal_dict = thermal_service.read_ini(area_id)

            for thermal_data in thermal_dict.values():
                thermal_cluster = ThermalCluster(
                    thermal_service=thermal_service,
                    area_id=area_id,
                    name=str(thermal_data.pop("name")),
                    properties=parse_thermal_cluster_local(thermal_service.study_version, thermal_data),
                )

                thermals.setdefault(area_id, {})[thermal_cluster.id] = thermal_cluster

    return thermals


def _read_renewables(renewable_service: RenewableLocalService) -> dict[str, dict[str, RenewableCluster]]:
    renewables: dict[str, dict[str, RenewableCluster]] = {}
    cluster_path = renewable_service.config.study_path / "input" / "renewables" / "clusters"
    if not cluster_path.exists():
        return {}
    for folder in cluster_path.iterdir():
        if folder.is_dir():
            area_id = folder.name

            renewable_dict = renewable_service.read_ini(area_id)

            for renewable_data in renewable_dict.values():
                renewable_cluster = RenewableCluster(
                    renewable_service=renewable_service,
                    area_id=area_id,
                    name=str(renewable_data.pop("name")),
                    properties=parse_renewable_cluster_local(renewable_service.study_version, renewable_data),
                )

                renewables.setdefault(area_id, {})[renewable_cluster.id] = renewable_cluster

    return renewables


def _read_st_storages(st_storage_service: ShortTermStorageLocalService) -> dict[str, dict[str, STStorage]]:
    st_storages: dict[str, dict[str, STStorage]] = {}
    cluster_path = st_storage_service.config.study_path / "input" / "st-storage" / "clusters"
    if not cluster_path.exists():
        return {}

    constraints = {}
    if st_storage_service.study_version >= STUDY_VERSION_9_2:
        constraints = st_storage_service.read_constraints()

    for folder in cluster_path.iterdir():
        if folder.is_dir():
            area_id = folder.name

            storage_dict = st_storage_service.read_ini(area_id)

            for storage_data in storage_dict.values():
                storage_name = str(storage_data.pop("name"))
                storage_properties = parse_st_storage_local(st_storage_service.study_version, storage_data)
                storage_id = transform_name_to_id(storage_name)
                relative_constraints = constraints.get(area_id, {}).get(storage_id, {})
                st_storage = STStorage(
                    storage_service=st_storage_service,
                    area_id=area_id,
                    name=storage_name,
                    properties=storage_properties,
                    constraints=relative_constraints,
                )
                st_storages.setdefault(area_id, {})[storage_id] = st_storage

    return st_storages
