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
    AreaProperties,
    AreaUi,
    ConstraintTerm,
    HydroProperties,
    PlaylistParameters,
    STStorageAdditionalConstraint,
)
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, StudyCreationError, StudyImportError, StudyMoveError
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import BindingConstraint, ConstraintTermData
from antares.craft.model.hydro import InflowStructure
from antares.craft.model.link import Link
from antares.craft.model.output import Output
from antares.craft.model.renewable import RenewableCluster
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.st_storage import STStorage
from antares.craft.model.study import Study
from antares.craft.model.thermal import ThermalCluster
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.api_services.models.area import AreaPropertiesAPI
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.api_services.models.hydro import HydroInflowStructureAPI, HydroPropertiesAPI
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
    parse_xpansion_constraints_api,
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
    BaseBindingConstraintService,
    BaseLinkService,
    BaseOutputService,
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


def import_study_api(api_config: APIconf, study_path: Path, destination_path: Optional[Path] = None) -> "Study":
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


def create_variant_api(api_config: APIconf, study_id: str, variant_name: str) -> "Study":
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



def read_study_api(api_config: APIconf, study_id: str) -> "Study":
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

    # Outputs
    study._outputs = _read_outputs(json_api, services.output_service)

    ###### XPANSION ########
    if "xpansion" not in json_api:
        study._xpansion_configuration = None
    else:
        xpansion_api = json_api.pop("xpansion")

    xp_config = json_api.pop("xp_settings")
    if not xp_config:
        study._xpansion_configuration = None
    else:
        # Settings
        settings, sensitivity = parse_xpansion_settings_api(xp_config)

        # Candidates
        api_cdts = json_api.pop("xp_cdt")
        candidates = {}
        for cdt_api in api_cdts:
            cdt = parse_xpansion_candidate_api(cdt_api)
            candidates[cdt.name] = cdt

        # Constraints
        xp_constraints = {}
        if settings.additional_constraints:
            xp_constraints = parse_xpansion_constraints_api(json_api.pop("xp_contraint"))

        study._xpansion_configuration = XpansionConfiguration(
            xpansion_service=services.xpansion_service,
            settings=settings,
            sensitivity=sensitivity,
            candidates=candidates,
            constraints=xp_constraints,
        )

    # Settings
    study._settings = _read_settings(json_api)

    ###### AREAS ########

    # Thermals
    thermals: dict[str, dict[str, ThermalCluster]] = {}

    for key, thermal in json_api.pop("thermal").items():
        area_id, thermal_id = key.split(" / ")
        thermal_props = ThermalClusterPropertiesAPI.model_validate(thermal).to_user_model()
        thermal_cluster = ThermalCluster(services.thermal_service, area_id, thermal_id, thermal_props)

        thermals.setdefault(area_id, {})[thermal_cluster.id] = thermal_cluster

    # Renewables
    renewables: dict[str, dict[str, RenewableCluster]] = {}

    for key, renewable in json_api.pop("renewable").items():
        area_id, renewable_id = key.split(" / ")
        renewable_props = RenewableClusterPropertiesAPI.model_validate(renewable).to_user_model()
        renewable_cluster = RenewableCluster(services.renewable_service, area_id, renewable_id, renewable_props)

        renewables.setdefault(area_id, {})[renewable_cluster.id] = renewable_cluster

    # STS
    constraints_dict: dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]] = {}
    for key, constraint_api in json_api.pop("sts_c").items():
        area_id, storage_id, constraint_id = key.split(" / ")
        args = {"id": constraint_id, "name": constraint_id, **constraint_api}
        constraint = parse_st_storage_constraint_api(args)
        constraints_dict.setdefault(area_id, {}).setdefault(storage_id, {})[constraint.id] = constraint

    storages: dict[str, dict[str, STStorage]] = {}

    for key, storage in json_api.pop("sts").items():
        area_id, storage_id = key.split(" / ")
        storage_props = parse_st_storage_api(storage)
        sts_constraints = constraints_dict.get(area_id, {}).get(storage_id, {})
        st_storage = STStorage(services.short_term_storage_service, area_id, storage_id, storage_props, sts_constraints)

        storages.setdefault(area_id, {})[st_storage.id] = st_storage

    # Hydro
    hydro_dict: dict[str, tuple[HydroProperties, InflowStructure]] = {}
    for area_id, api_content in json_api.pop("hydro").items():
        # Inflow
        api_inflow = api_content["inflowStructure"]
        inflow_structure = HydroInflowStructureAPI.model_validate(api_inflow).to_user_model()
        # Properties
        api_properties = api_content["managementOptions"]
        hydro_properties = HydroPropertiesAPI.model_validate(api_properties).to_user_model()

        hydro_dict[area_id] = (hydro_properties, inflow_structure)

    # Area properties
    area_properties: dict[str, AreaProperties] = {}
    for area_id, area_properties_api in json_api.pop("areas").items():
        area_properties[area_id] = AreaPropertiesAPI.model_validate(area_properties_api).to_user_model()

    # Area ui
    area_ui: dict[str, AreaUi] = {}
    for area_id, props in json_api.pop("areas_ui").items():
        api_ui = props["ui"]
        ui = AreaUi(x=api_ui["x"], y=api_ui["y"], color_rgb=[api_ui["color_r"], api_ui["color_g"], api_ui["color_b"]])
        area_ui[area_id] = ui

    all_areas = {}
    for area_id, ui in area_ui.items():
        area_obj = Area(
            area_id,
            services.area_service,
            services.short_term_storage_service,
            services.thermal_service,
            services.renewable_service,
            services.hydro_service,
            ui=ui,
        )
        # Fill the created object with the right values
        area_obj._properties = area_properties[area_obj.id]
        area_obj._thermals = thermals.get(area_obj.id, {})
        area_obj._renewables = renewables.get(area_obj.id, {})
        area_obj._st_storages = storages.get(area_obj.id, {})
        area_obj.hydro._properties = hydro_dict[area_obj.id][0]
        area_obj.hydro._inflow_structure = hydro_dict[area_obj.id][1]

        all_areas[area_obj.id] = area_obj

    study._areas = all_areas

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

def _read_binding_constraints(body: dict[str, Any], bc_service: BaseBindingConstraintService) -> dict[str, BindingConstraint]:
    constraints = {}
    bcs_api = body["binding_constraints"]
    for bc_api in bcs_api:
        constraint_name = bc_api.pop("name")
        del bc_api["id"]

        api_terms = bc_api.pop("terms")
        api_properties = BindingConstraintPropertiesAPI.model_validate(bc_api)
        bc_properties = api_properties.to_user_model()

        terms: list[ConstraintTerm] = []
        for api_term in api_terms:
            term_data = ConstraintTermData.from_dict(api_term["data"])
            terms.append(ConstraintTerm(weight=api_term["weight"], offset=api_term["offset"], data=term_data))

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

def _read_outputs(body: dict[str, Any], output_service: BaseOutputService) -> dict[str, Output]:
    outputs = {}
    api_outputs = body["outputs"]
    for api_otp in api_outputs:
        output = Output(output_service=output_service, name=api_otp["name"], archived=api_otp["archived"])
        outputs[output.name] = output

    return outputs