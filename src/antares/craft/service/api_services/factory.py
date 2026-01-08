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
import io

from pathlib import Path, PurePath
from typing import Any, Optional

from antares.craft import (
    AreaUi,
    ConstraintSign,
    ConstraintTerm,
    PlaylistParameters,
    STStorageAdditionalConstraint,
    XpansionConstraint,
)
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, StudyCreationError, StudyImportError, StudyMoveError
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import BindingConstraint, ConstraintTermData
from antares.craft.model.hydro import Hydro
from antares.craft.model.link import Link
from antares.craft.model.renewable import RenewableCluster
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.st_storage import STStorage
from antares.craft.model.study import Study
from antares.craft.model.thermal import ThermalCluster
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.api_services.models.area import AreaPropertiesAPI
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.api_services.models.hydro import (
    HydroInflowStructureAPI,
    HydroPropertiesAPI,
    parse_hydro_allocation_api,
)
from antares.craft.service.api_services.models.link import LinkPropertiesAndUiAPI
from antares.craft.service.api_services.models.renewable import RenewableClusterPropertiesAPI
from antares.craft.service.api_services.models.settings import (
    parse_adequacy_patch_parameters_api,
    parse_advanced_and_seed_parameters_api,
    parse_general_parameters_api,
    parse_optimization_parameters_api,
    parse_thematic_trimming_api,
)
from antares.craft.service.api_services.models.st_storage import parse_st_storage_api, parse_st_storage_constraint_api
from antares.craft.service.api_services.models.thermal import ThermalClusterPropertiesAPI
from antares.craft.service.api_services.models.xpansion import (
    parse_xpansion_candidate_api,
    parse_xpansion_settings_api,
)
from antares.craft.service.api_services.services.area import AreaApiService
from antares.craft.service.api_services.services.binding_constraint import BindingConstraintApiService
from antares.craft.service.api_services.services.hydro import HydroApiService
from antares.craft.service.api_services.services.link import LinkApiService
from antares.craft.service.api_services.services.output import OutputApiService
from antares.craft.service.api_services.services.renewable import RenewableApiService
from antares.craft.service.api_services.services.run import RunApiService
from antares.craft.service.api_services.services.settings import StudySettingsAPIService
from antares.craft.service.api_services.services.st_storage import ShortTermStorageApiService
from antares.craft.service.api_services.services.study import StudyApiService
from antares.craft.service.api_services.services.thermal import ThermalApiService
from antares.craft.service.api_services.services.xpansion import XpansionAPIService
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseBindingConstraintService,
    BaseLinkService,
    BaseXpansionService,
    StudyServices,
)


def create_api_services(config: APIconf, study_id: str = "") -> StudyServices:
    storage_service = ShortTermStorageApiService(config, study_id)
    thermal_service = ThermalApiService(config, study_id)
    renewable_service = RenewableApiService(config, study_id)
    hydro_service = HydroApiService(config, study_id)
    area_service = AreaApiService(config, study_id, storage_service, thermal_service, renewable_service, hydro_service)
    link_service = LinkApiService(config, study_id)
    output_service = OutputApiService(config, study_id)
    study_service = StudyApiService(config, study_id, output_service)
    bc_service = BindingConstraintApiService(config, study_id)
    run_service = RunApiService(config, study_id)
    settings_service = StudySettingsAPIService(config, study_id)
    xpansion_service = XpansionAPIService(config, study_id)
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
        short_term_storage_service=storage_service,
        xpansion_service=xpansion_service,
    )


def create_study_api(
    study_name: str,
    version: str,
    api_config: APIconf,
    parent_path: Optional[Path] = None,
) -> Study:
    """
    Args:
        study_name: antares study name to be created
        version: antares version
        api_config: host and token config for API

    Raises:
        MissingTokenError if api_token is missing
        StudyCreationError if an HTTP Exception occurs
    """

    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"

    try:
        url = f"{base_url}/studies?name={study_name}&version={version}"
        response = wrapper.post(url)
        study_id = response.json()
        study = read_study_api(api_config, study_id)
        # Move part
        if parent_path:
            study.move(parent_path)
            url = f"{base_url}/studies/{study_id}"
            json_study = wrapper.get(url).json()
            folder = json_study.pop("folder")
            study.path = PurePath(folder) if folder else PurePath(".")
        return study
    except (APIError, StudyMoveError) as e:
        raise StudyCreationError(study_name, e.message) from e


def import_study_api(api_config: APIconf, study_path: Path, destination_path: Optional[Path] = None) -> Study:
    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"

    if study_path.suffix not in {".zip", ".7z"}:
        raise StudyImportError(
            study_path.name, f"File doesn't have the right extensions (.zip/.7z): {study_path.suffix}"
        )

    try:
        files = {"study": io.BytesIO(study_path.read_bytes())}
        url = f"{base_url}/studies/_import"
        study_id = wrapper.post(url, files=files).json()

        study = read_study_api(api_config, study_id)
        if destination_path is not None:
            study.move(destination_path)

        return study
    except APIError as e:
        raise StudyImportError(study_path.name, e.message) from e


def create_variant_api(api_config: APIconf, study_id: str, variant_name: str) -> Study:
    """
    Creates a variant from a study_id
    Args:
        api_config: API configuration
        study_id: The id of the study to create a variant of
        variant_name: the name of the new variant
    Returns: The variant in the form of a Study object
    """
    services = create_api_services(api_config, study_id)
    return services.study_service.create_variant(variant_name)


def read_study_api(api_config: APIconf, study_id: str) -> Study:
    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"
    json_api = wrapper.get(f"{base_url}/studies/{study_id}/data").json()

    services = create_api_services(api_config, study_id)

    # Metadata
    study = _read_study_metadata(json_api, services)

    # Links
    study._links = _read_links(json_api, services.link_service)

    # Binding constraints
    study._binding_constraints = _read_binding_constraints(json_api, services.bc_service)

    # Xpansion
    study._xpansion_configuration = _read_xpansion(json_api, services.xpansion_service)

    # Settings
    study._settings = _read_settings(json_api)

    # Areas
    study._areas = _read_areas(json_api, services.area_service)

    # Outputs
    study._read_outputs()

    return study


def _read_links(body: dict[str, Any], link_service: BaseLinkService) -> dict[str, Link]:
    links = {}
    links_api = body["links"]
    for link in links_api:
        area_from = link.pop("area1")
        area_to = link.pop("area2")

        api_response = LinkPropertiesAndUiAPI.model_validate(link)
        link_properties = api_response.to_properties_user_model()
        link_ui = api_response.to_ui_user_model()

        link = Link(area_from, area_to, link_service, link_properties, link_ui)
        links[link.id] = link

    return links


def _read_binding_constraints(
    body: dict[str, Any], bc_service: BaseBindingConstraintService
) -> dict[str, BindingConstraint]:
    constraints = {}
    bcs_api = body["bindingConstraints"]
    for bc_api in bcs_api:
        constraint_name = bc_api.pop("name")
        del bc_api["id"]

        api_terms = bc_api.pop("terms")
        api_properties = BindingConstraintPropertiesAPI.model_validate(bc_api)
        bc_properties = api_properties.to_user_model()

        terms: list[ConstraintTerm] = []
        for api_term in api_terms:
            term_data = ConstraintTermData.from_dict(api_term["data"])
            terms.append(ConstraintTerm(weight=api_term["weight"], offset=api_term.get("offset", 0), data=term_data))

        bc = BindingConstraint(constraint_name, bc_service, bc_properties, terms)
        constraints[bc.id] = bc

    return constraints


def _read_settings(body: dict[str, Any]) -> StudySettings:
    settings_api = body["settings"]
    nb_ts_thermal = settings_api["timeSeries"]["thermal"]["number"]
    general_parameters = parse_general_parameters_api(settings_api["general"], nb_ts_thermal)
    thematic_trimming_parameters = parse_thematic_trimming_api(settings_api["thematicTrimming"])
    optimization_parameters = parse_optimization_parameters_api(settings_api["optimization"])
    adequacy_patch_parameters = parse_adequacy_patch_parameters_api(settings_api["adequacyPatch"])
    advanced_parameters, seed_parameters = parse_advanced_and_seed_parameters_api(settings_api["advancedParameters"])

    user_playlist = {}
    api_playlist = settings_api["playlist"].get("years", {})
    for key, value in api_playlist.items():
        user_playlist[int(key)] = PlaylistParameters(**value)

    return StudySettings(
        general_parameters=general_parameters,
        optimization_parameters=optimization_parameters,
        seed_parameters=seed_parameters,
        advanced_parameters=advanced_parameters,
        adequacy_patch_parameters=adequacy_patch_parameters,
        playlist_parameters=user_playlist,
        thematic_trimming_parameters=thematic_trimming_parameters,
    )


def _read_study_metadata(body: dict[str, Any], services: StudyServices) -> Study:
    study_metadata = body["metadata"]
    study_name = study_metadata["name"]
    study_version = study_metadata["version"]
    folder = study_metadata.get("folder")
    pure_path = PurePath(folder) if folder else PurePath(".")

    return Study(study_name, study_version, services, pure_path)


def _read_areas(body: dict[str, Any], area_service: BaseAreaService) -> dict[str, Area]:
    all_areas = {}
    areas_api = body["areas"]
    for area_api in areas_api:
        area_name, area_id = area_api["name"], area_api["id"]
        area_properties = AreaPropertiesAPI.model_validate(area_api["properties"]).to_user_model()
        ui_api = area_api["ui"]
        area_ui = AreaUi(x=ui_api["x"], y=ui_api["y"], color_rgb=ui_api["colorRgb"])

        area = Area(
            area_name,
            area_service,
            area_service.storage_service,
            area_service.thermal_service,
            area_service.renewable_service,
            area_service.hydro_service,
            properties=area_properties,
            ui=area_ui,
        )

        # Thermals
        thermals: dict[str, ThermalCluster] = {}

        for thermal in area_api["thermals"]:
            thermal_name = thermal["name"]
            del thermal["id"]

            thermal_props = ThermalClusterPropertiesAPI.model_validate(thermal).to_user_model()
            thermal_cluster = ThermalCluster(area_service.thermal_service, area_id, thermal_name, thermal_props)

            thermals[thermal_cluster.id] = thermal_cluster

        area._thermals = thermals

        # Renewables
        renewables: dict[str, RenewableCluster] = {}

        for renewable in area_api["renewables"]:
            renew_name = renewable["name"]
            del renewable["id"]

            renewable_props = RenewableClusterPropertiesAPI.model_validate(renewable).to_user_model()
            renewable_cluster = RenewableCluster(area_service.renewable_service, area_id, renew_name, renewable_props)

            renewables[renewable_cluster.id] = renewable_cluster

        area._renewables = renewables

        # Short-term storages
        storages: dict[str, STStorage] = {}
        for storage_api in area_api["stStorages"]:
            # Constraints
            constraints_dict: dict[str, STStorageAdditionalConstraint] = {}

            sts_api_constraints = storage_api.pop("constraints")
            for sts_api_constraint in sts_api_constraints:
                sts_constraint = parse_st_storage_constraint_api(sts_api_constraint)
                constraints_dict[sts_constraint.id] = sts_constraint

            # Properties
            sts_name = storage_api["name"]
            del storage_api["id"]
            sts_props = parse_st_storage_api(storage_api)

            st_storage = STStorage(area_service.storage_service, area_id, sts_name, sts_props, constraints_dict)
            storages[st_storage.id] = st_storage

        area._st_storages = storages

        # Hydro
        hydro_api = area_api["hydro"]
        inflow_structure = HydroInflowStructureAPI.model_validate(hydro_api["inflowStructure"]).to_user_model()
        hydro_properties = HydroPropertiesAPI.model_validate(hydro_api["managementOptions"]).to_user_model()
        hydro_allocation = parse_hydro_allocation_api(hydro_api["allocation"])

        area._hydro = Hydro(area_service.hydro_service, area_id, hydro_properties, inflow_structure, hydro_allocation)

        all_areas[area_id] = area

    return all_areas


def _read_xpansion(body: dict[str, Any], xp_service: BaseXpansionService) -> XpansionConfiguration | None:
    if "xpansion" not in body:
        return None

    xpansion_api = body["xpansion"]

    settings, sensitivity = parse_xpansion_settings_api(xpansion_api["settings"])

    candidates = {}
    for candidate_api in xpansion_api["candidates"]:
        cdt = parse_xpansion_candidate_api(candidate_api)
        candidates[cdt.name] = cdt

    xp_constraints = {}
    for constraint_api in xpansion_api["constraints"]:
        constraint = XpansionConstraint(
            name=constraint_api["name"],
            sign=ConstraintSign(constraint_api["sign"]),
            right_hand_side=constraint_api["rightHandSide"],
            candidates_coefficients=constraint_api["candidatesCoefficients"],
        )
        xp_constraints[constraint.name] = constraint

    return XpansionConfiguration(
        xpansion_service=xp_service,
        settings=settings,
        sensitivity=sensitivity,
        candidates=candidates,
        constraints=xp_constraints,
    )
