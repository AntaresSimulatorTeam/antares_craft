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
from types import MappingProxyType
from typing import List, Optional, Union

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import APIError, LinkCreationError, StudyCreationError
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    ConstraintTerm,
)
from antares.craft.model.link import Link, LinkProperties, LinkUi
from antares.craft.model.output import Output
from antares.craft.model.settings.study_settings import DefaultStudySettings, StudySettings, StudySettingsLocal
from antares.craft.model.settings.time_series import correlation_defaults
from antares.craft.model.simulation import AntaresSimulationParameters, Job
from antares.craft.service.api_services.study_api import _returns_study_settings
from antares.craft.service.base_services import BaseStudyService
from antares.craft.service.service_factory import ServiceFactory
from antares.craft.tools.ini_tool import IniFile, IniFileTypes

"""
The study module defines the data model for antares study.
It represents a power system involving areas and power flows
between these areas.
Optional attribute _api_id defined for studies being stored in web
_study_path if stored in a disk
"""


def create_study_api(
    study_name: str, version: str, api_config: APIconf, settings: Optional[StudySettings] = None
) -> "Study":
    """
    Args:
        study_name: antares study name to be created
        version: antares version
        api_config: host and token config for API
        settings: study settings. If not provided, AntaresWeb will use its default values.

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
        study_settings = _returns_study_settings(base_url, study_id, wrapper, False, settings)

    except APIError as e:
        raise StudyCreationError(study_name, e.message) from e
    return Study(study_name, version, ServiceFactory(api_config, study_id), study_settings)


def create_study_local(
    study_name: str,
    version: str,
    parent_directory: str,
    settings: StudySettingsLocal = StudySettingsLocal(),
) -> "Study":
    """
    Create a directory structure for the study with empty files.

    Args:
        study_name: antares study name to be created
        version: antares version for study
        parent_directory: Local directory to store the study in.
        settings: study settings. If not provided, AntaresCraft will use its default values.

    Raises:
        FileExistsError if the study already exists in the given location
    """
    local_config = LocalConfiguration(Path(parent_directory), study_name)

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

    local_settings = StudySettingsLocal.model_validate(settings)
    local_settings_file = IniFile(study_directory, IniFileTypes.GENERAL)
    local_settings_file.ini_dict = local_settings.model_dump(exclude_none=True, by_alias=True)
    local_settings_file.write_ini_file()

    # Create various .ini files for the study
    _create_correlation_ini_files(local_settings, study_directory)

    logging.info(f"Study successfully created: {study_name}")
    return Study(
        name=study_name,
        version=version,
        service_factory=ServiceFactory(config=local_config, study_name=study_name),
        settings=local_settings,
    )


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

    study_antares = IniFile(study_directory, IniFileTypes.ANTARES)

    study_params = study_antares.ini_dict["antares"]

    local_config = LocalConfiguration(study_directory.parent, study_directory.name)

    return Study(
        name=study_params["caption"],
        version=study_params["version"],
        service_factory=ServiceFactory(config=local_config, study_name=study_params["caption"]),
    )


def read_study_api(api_config: APIconf, study_id: str) -> "Study":
    session = api_config.set_up_api_conf()
    wrapper = RequestWrapper(session)
    base_url = f"{api_config.get_host()}/api/v1"
    json_study = wrapper.get(f"{base_url}/studies/{study_id}").json()

    study_name = json_study.pop("name")
    study_version = str(json_study.pop("version"))

    study_settings = _returns_study_settings(base_url, study_id, wrapper, False, None)
    study = Study(study_name, study_version, ServiceFactory(api_config, study_id, study_name), study_settings)

    study.read_areas()
    study.read_outputs()
    study.read_binding_constraints()

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
    factory = ServiceFactory(api_config, study_id)
    api_service = factory.create_study_service()

    return api_service.create_variant(variant_name)


class Study:
    def __init__(
        self,
        name: str,
        version: str,
        service_factory: ServiceFactory,
        settings: Union[StudySettings, StudySettingsLocal, None] = None,
    ):
        self.name = name
        self.version = version
        self._study_service = service_factory.create_study_service()
        self._area_service = service_factory.create_area_service()
        self._link_service = service_factory.create_link_service()
        self._run_service = service_factory.create_run_service()
        self._binding_constraints_service = service_factory.create_binding_constraints_service()
        self._settings = DefaultStudySettings.model_validate(settings if settings is not None else StudySettings())
        self._areas: dict[str, Area] = dict()
        self._links: dict[str, Link] = dict()
        self._binding_constraints: dict[str, BindingConstraint] = dict()
        self._outputs: dict[str, Output] = dict()

    @property
    def service(self) -> BaseStudyService:
        return self._study_service

    def read_areas(self) -> list[Area]:
        """
        Synchronize the internal study object with the actual object written in an antares study
        Returns: the synchronized area list
        """
        area_list = self._area_service.read_areas()
        self._areas = {area.id: area for area in area_list}
        return area_list

    def read_links(self) -> list[Link]:
        return self._link_service.read_links()

    def get_areas(self) -> MappingProxyType[str, Area]:
        return MappingProxyType(dict(sorted(self._areas.items())))

    def get_links(self) -> MappingProxyType[str, Link]:
        return MappingProxyType(self._links)

    def get_settings(self) -> DefaultStudySettings:
        return self._settings

    def get_binding_constraints(self) -> MappingProxyType[str, BindingConstraint]:
        return MappingProxyType(self._binding_constraints)

    def create_area(
        self, area_name: str, *, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        area = self._area_service.create_area(area_name, properties, ui)
        self._areas[area.id] = area
        return area

    def delete_area(self, area: Area) -> None:
        self._area_service.delete_area(area.id)
        self._areas.pop(area.id)

    def create_link(
        self,
        *,
        area_from: str,
        area_to: str,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
    ) -> Link:
        temp_link = Link(area_from, area_to, link_service=None)
        area_from, area_to = sorted([area_from, area_to])
        area_from_id = temp_link.area_from_id
        area_to_id = temp_link.area_to_id

        if area_from_id == area_to_id:
            raise LinkCreationError(area_from, area_to, "A link cannot start and end at the same area")

        missing_areas = [area for area in [area_from_id, area_to_id] if area not in self._areas]
        if missing_areas:
            raise LinkCreationError(area_from, area_to, f"{', '.join(missing_areas)} does not exist")

        if temp_link.id in self._links:
            raise LinkCreationError(area_from, area_to, f"A link from {area_from} to {area_to} already exists")

        link = self._link_service.create_link(area_from_id, area_to_id, properties, ui)
        self._links[link.id] = link
        return link

    def delete_link(self, link: Link) -> None:
        self._link_service.delete_link(link)
        self._links.pop(link.id)

    def create_binding_constraint(
        self,
        *,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[List[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
        """
        Create a new binding constraint and store it.

        Args:
            name (str): The name of the binding constraint.
            properties (Optional[BindingConstraintProperties]): Optional properties for the constraint.
            terms (Optional[List[ConstraintTerm]]): Optional list of terms for the constraint.
            less_term_matrix (Optional[pd.DataFrame]): Optional less-than term matrix.
            equal_term_matrix (Optional[pd.DataFrame]): Optional equality term matrix.
            greater_term_matrix (Optional[pd.DataFrame]): Optional greater-than term matrix.

        Returns:
            BindingConstraint: The created binding constraint.
        """
        binding_constraint = self._binding_constraints_service.create_binding_constraint(
            name, properties, terms, less_term_matrix, equal_term_matrix, greater_term_matrix
        )
        self._binding_constraints[binding_constraint.id] = binding_constraint
        return binding_constraint

    def read_binding_constraints(self) -> list[BindingConstraint]:
        constraints = self._binding_constraints_service.read_binding_constraints()
        self._binding_constraints = {constraint.id: constraint for constraint in constraints}
        return constraints

    def update_settings(self, settings: StudySettings) -> None:
        new_settings = self._study_service.update_study_settings(settings)
        if new_settings:
            self._settings = new_settings

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        self._study_service.delete_binding_constraint(constraint)
        self._binding_constraints.pop(constraint.id)

    def delete(self, children: bool = False) -> None:
        self._study_service.delete(children)

    def create_variant(self, variant_name: str) -> "Study":
        """
        Creates a new variant for the study

        Args:
            variant_name: the name of the new variant
        Returns: The variant in the form of a Study object
        """
        return self._study_service.create_variant(variant_name)

    def run_antares_simulation(self, parameters: Optional[AntaresSimulationParameters] = None) -> Job:
        """
        Runs the Antares simulation.

        This method starts an antares simulation with the given parameters

        Returns: A job representing the simulation task
        """
        return self._run_service.run_antares_simulation(parameters)

    def wait_job_completion(self, job: Job, time_out: int = 172800) -> None:
        """
        Waits for the completion of a job

        Args:
            job: The job to wait for
            time_out: Time limit for waiting (seconds), default: 172800s

        Raises: SimulationTimeOutError if exceeded timeout
        """
        self._run_service.wait_job_completion(job, time_out)

    def read_outputs(self) -> list[Output]:
        """
        Load outputs into current study

        Returns: Output list
        """
        outputs = self._study_service.read_outputs()
        self._outputs = {output.name: output for output in outputs}
        return outputs

    def get_outputs(self) -> MappingProxyType[str, Output]:
        """
        Get outputs of current study

        Returns: read-only proxy of the (output_id, Output) mapping
        """
        return MappingProxyType(self._outputs)

    def get_output(self, output_id: str) -> Output:
        """
        Get a specific output

        Args:
            output_id: id of the output to get

        Returns: Output with the output_id

        Raises: KeyError if it doesn't exist
        """
        return self._outputs[output_id]


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


def _create_correlation_ini_files(local_settings: StudySettingsLocal, study_directory: Path) -> None:
    fields_to_check = ["hydro", "load", "solar", "wind"]
    correlation_inis_to_create = [
        (
            field + "_correlation",
            getattr(IniFileTypes, field.upper() + "_CORRELATION_INI"),
            field,
        )
        for field in fields_to_check
    ]

    for correlation, file_type, field in correlation_inis_to_create:
        ini_file = IniFile(
            study_directory,
            file_type,
            ini_contents=correlation_defaults(
                season_correlation=getattr(local_settings.time_series_parameters, field).season_correlation,
            ),
        )
        ini_file.write_ini_file()
