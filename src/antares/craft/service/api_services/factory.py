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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import APIError, StudyCreationError, StudyImportError, StudyMoveError
from antares.craft.model.study import Study
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
