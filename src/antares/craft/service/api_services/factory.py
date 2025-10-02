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
from typing import Optional

from antares.craft import ConstraintTerm
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, StudyCreationError, StudyImportError, StudyMoveError
from antares.craft.model.binding_constraint import BindingConstraint, ConstraintTermData
from antares.craft.model.link import Link
from antares.craft.model.output import Output
from antares.craft.model.study import Study
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.api_services.models.link import LinkPropertiesAndUiAPI
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
        # Settings part
        study = Study(study_name, version, create_api_services(api_config, study_id))
        study._read_settings()
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


def load_study_api(api_config: APIconf, study_id: str) -> "Study":
    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"
    json_api = wrapper.get(f"{base_url}/studies/{study_id}/craft").json()

    services = create_api_services(api_config, study_id)

    ####### STUDY #######
    study_name = json_api.pop("name")
    study_version = json_api.pop("version")
    path = json_api.pop("path")
    pure_path = PurePath(path) if path else PurePath(".")

    study = Study(study_name, study_version, services, pure_path)

    ####### LINKS #######
    links = {}
    links_api = json_api.pop("links")
    for props in links_api.values():
        area_from = props.pop("area1")
        area_to = props.pop("area2")

        api_response = LinkPropertiesAndUiAPI.model_validate(props)
        link_properties = api_response.to_properties_user_model()
        link_ui = api_response.to_ui_user_model()

        link = Link(area_from, area_to, services.link_service, link_properties, link_ui)
        links[link.id] = link

    study._links = links

    ####### BINDING CONSTRAINTS #######
    constraints = {}
    bcs_api = json_api.pop("bcs")
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

        bc = BindingConstraint(constraint_name, services.bc_service, bc_properties, terms)
        constraints[bc.id] = bc

    study._binding_constraints = constraints

    ####### OUTPUTS #######
    outputs = {}
    api_outputs = json_api.pop("outputs")
    for output_id, output_props in api_outputs.items():
        output = Output(output_service=services.output_service, name=output_id, archived=output_props["archived"])
        outputs[output.name] = output

    study._outputs = outputs

    ###### XPANSION ########
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

    ###### TODO ########

    print(json_api)

    """
    obj = {
        "areas": self.table_mode_manager.get_table_data(interface, TableModeType.AREA, []),
        "links": self.table_mode_manager.get_table_data(interface, TableModeType.LINK, []),
        "bcs": self.table_mode_manager.get_table_data(interface, TableModeType.BINDING_CONSTRAINT, []),
        "renewable": self.table_mode_manager.get_table_data(interface, TableModeType.RENEWABLE, []),
        "thermal": self.table_mode_manager.get_table_data(interface, TableModeType.THERMAL, []),
        "sts": self.table_mode_manager.get_table_data(interface, TableModeType.ST_STORAGE, []),
        "sts_c": self.table_mode_manager.get_table_data(
            interface, TableModeType.ST_STORAGE_ADDITIONAL_CONSTRAINTS, []
        ),
        "hydro": self.hydro_manager.get_all_hydro_properties(interface),
        "xp_settings": xp_settings,
        "ts_config": self.ts_config_manager.get_timeseries_configuration(interface),
        "general_config": self.general_manager.get_general_config(interface),
        "adv_config": self.advanced_parameters_manager.get_advanced_parameters(interface),
        "playlist": self.playlist_manager.get_playlist(interface),
        "thematic_config": self.thematic_trimming_manager.get_thematic_trimming(interface),
        "opt_config": self.optimization_manager.get_optimization_preferences(interface),
        "adequacy_config": self.adequacy_patch_manager.get_adequacy_patch_parameters(interface),
        "version": study.version,
        "name": study.name,
        "path": study.path,
        "outputs": interface.get_files().config.outputs,
    }

    if xp_settings:
        obj["xp_cdt"] = self.xpansion_manager.get_candidates(interface)
        if xp_settings.additional_constraints:
            obj["xp_contraint"] = self.xpansion_manager.get_resource_content(
                interface, XpansionResourceFileType.CONSTRAINTS, xp_settings.additional_constraints
            )
    """

    study._read_settings()
    study._read_areas()

    return study


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


def read_study_api(api_config: APIconf, study_id: str) -> "Study":
    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"
    json_study = wrapper.get(f"{base_url}/studies/{study_id}").json()

    study_name = json_study.pop("name")
    study_version = str(json_study.pop("version"))
    path = json_study.pop("folder")
    pure_path = PurePath(path) if path else PurePath(".")

    study = Study(study_name, study_version, create_api_services(api_config, study_id), pure_path)

    study._read_settings()
    study._read_areas()
    study._read_links()
    study._read_outputs()
    study._read_binding_constraints()
    study._read_xpansion_configuration()

    return study


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
