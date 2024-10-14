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
from typing import Optional, Dict, List, Any

import pandas as pd

from antares.api_conf.api_conf import APIconf
from antares.api_conf.request_wrapper import RequestWrapper
from antares.config.local_configuration import LocalConfiguration
from antares.exceptions.exceptions import APIError, StudyCreationError
from antares.model.area import Area, AreaProperties, AreaUi
from antares.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    ConstraintTerm,
)
from antares.model.link import Link, LinkUi, LinkProperties
from antares.model.settings import StudySettings
from antares.service.api_services.study_api import _returns_study_settings
from antares.service.base_services import BaseStudyService
from antares.service.service_factory import ServiceFactory, ServiceReader
from antares.tools.ini_tool import IniFile, IniFileTypes

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


def _verify_study_already_exists(study_directory: Path) -> None:
    if os.path.exists(study_directory):
        raise FileExistsError(f"Study {study_directory} already exists.")


def _directories_can_be_read(local_path: Path) -> None:
    if local_path.is_dir():
        try:
            for item in local_path.iterdir():
                if item.is_dir():
                    next(item.iterdir())
        except PermissionError:
            raise PermissionError(f"Some content cannot be accessed in {local_path}")


def create_study_local(
    study_name: str, version: str, local_config: LocalConfiguration, settings: Optional[StudySettings] = None
) -> "Study":
    """
    Create a directory structure for the study with empty files.
    Args:
        study_name: antares study name to be created
        version: antares version for study
        local_config: Local configuration options for example directory in which to story the study
        settings: study settings. If not provided, AntaresWeb will use its default values.

    Raises:
        FileExistsError if the study already exists in the given location
        ValueError if the provided directory does not exist

    """

    def _directory_not_exists(local_path: Path) -> None:
        if local_path is None or not os.path.exists(local_path):
            raise ValueError(f"Provided directory {local_path} does not exist.")

    _directory_not_exists(local_config.local_path)

    study_directory = local_config.local_path / study_name

    _verify_study_already_exists(study_directory)

    # Create the main study directory
    os.makedirs(study_directory, exist_ok=True)

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

    # Create subdirectories
    subdirectories = ["input", "layers", "output", "setting", "user"]
    for subdirectory in subdirectories:
        subdirectory_path = os.path.join(study_directory, subdirectory)
        os.makedirs(subdirectory_path, exist_ok=True)

    logging.info(f"Study successfully created: {study_name}")
    return Study(
        name=study_name,
        version=version,
        service_factory=ServiceFactory(config=local_config, study_name=study_name),
        settings=settings,
        mode="create",
    )


def read_study_local(study_name: str, version: str, local_config: LocalConfiguration) -> "Study":
    """
    Create a directory structure for the study with empty files.
    Args:
        study_name: antares study name to read
        version: antares version for study
        settings: study settings. If not provided, AntaresWeb will use its default values.

    Raises:
        PermissionError if the study cannot be read
        ValueError if the provided directory does not exist

    """

    def _directory_not_exists(local_path: Path) -> None:
        if local_path is None or not os.path.exists(local_path):
            raise ValueError(f"Provided directory {local_path} does not exist.")

    local_path = Path(local_config.local_path)
    _directory_not_exists(local_path)
    study_directory = local_path / study_name
    _directories_can_be_read(study_directory)

    return Study(
        name=study_name,
        version=version,
        service_factory=ServiceReader(config=local_config, study_name=Path(study_name)),
        mode="read",
    )


class Study:
    def __init__(
        self,
        name: str,
        version: str,
        service_factory,
        settings: Optional[StudySettings] = None,
        mode: str = "create",
        # ini_files: Optional[dict[str, IniFile]] = None,
        **kwargs: Any,
    ):
        self.name = name
        self.version = version
        for argument in kwargs:
            if argument == "ini_files":
                self._ini_files: dict[str, IniFile] = kwargs[argument] or dict()
        if mode != "read":
            self._study_service = service_factory.create_study_service()
            self._area_service = service_factory.create_area_service()
            self._link_service = service_factory.create_link_service()
            self._binding_constraints_service = service_factory.create_binding_constraints_service()
            self._settings = settings or StudySettings()
            self._areas: Dict[str, Area] = dict()
            self._links: Dict[str, Link] = dict()
            self._binding_constraints: Dict[str, BindingConstraint] = dict()
        else:
            self._study_service = service_factory.read_study_service()
            # self._binding_constraints: Dict[str, BindingConstraint] = dict()
            # self._link_service = service_factory.create_link_service()
            self._areas: Dict[str, Area] = dict()
            self._links: Dict[str, Link] = dict()

    @property
    def service(self) -> BaseStudyService:
        return self._study_service

    def get_areas(self) -> MappingProxyType[str, Area]:
        return MappingProxyType(dict(sorted(self._areas.items())))

    def get_links(self) -> MappingProxyType[str, Link]:
        return MappingProxyType(self._links)

    def get_settings(self) -> StudySettings:
        return self._settings

    def get_binding_constraints(self) -> MappingProxyType[str, BindingConstraint]:
        return MappingProxyType(self._binding_constraints_service.binding_constraints)

    def create_area(
        self, area_name: str, *, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        area = self._area_service.create_area(area_name, properties, ui)
        self._areas[area.id] = area
        return area

    def delete_area(self, area: Area) -> None:
        self._area_service.delete_area(area)
        self._areas.pop(area.id)

    def create_link(
        self,
        *,
        area_from: Area,
        area_to: Area,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
        existing_areas: Optional[MappingProxyType[str, Area]] = None,
    ) -> Link:
        link = self._link_service.create_link(area_from, area_to, properties, ui, existing_areas)
        self._links[link.name] = link
        return link

    def delete_link(self, link: Link) -> None:
        self._link_service.delete_link(link)
        self._links.pop(link.name)

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
        return self._binding_constraints_service.create_binding_constraint(
            name, properties, terms, less_term_matrix, equal_term_matrix, greater_term_matrix
        )

    def update_settings(self, settings: StudySettings) -> None:
        new_settings = self._study_service.update_study_settings(settings)
        if new_settings:
            self._settings = new_settings

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        self._study_service.delete_binding_constraint(constraint)
        self._binding_constraints_service.binding_constraints.pop(constraint.id)

    def delete(self, children: bool = False) -> None:
        self._study_service.delete(children)
