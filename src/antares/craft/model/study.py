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

from pathlib import Path, PurePath
from types import MappingProxyType
from typing import List, Optional, cast

import pandas as pd

from antares.craft import APIconf
from antares.craft.exceptions.exceptions import (
    LinkCreationError,
)
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    ConstraintTerm,
)
from antares.craft.model.link import Link, LinkProperties, LinkUi
from antares.craft.model.output import Output
from antares.craft.model.settings.study_settings import StudySettings, StudySettingsUpdate
from antares.craft.model.simulation import AntaresSimulationParameters, Job
from antares.craft.service.base_services import BaseLinkService, BaseStudyService, StudyServices

"""
The study module defines the data model for antares study.
It represents a power system involving areas and power flows
between these areas.
Optional attribute _api_id defined for studies being stored in web
_study_path if stored in a disk
"""


class Study:
    def __init__(
        self,
        name: str,
        version: str,
        services: StudyServices,
        path: PurePath = PurePath("."),
    ):
        self.name = name
        self.version = version
        self.path = path
        self._study_service = services.study_service
        self._area_service = services.area_service
        self._link_service = services.link_service
        self._run_service = services.run_service
        self._binding_constraints_service = services.bc_service
        self._settings_service = services.settings_service
        self._settings = StudySettings()
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
        link_list = self._link_service.read_links()
        self._links = {link.id: link for link in link_list}
        return link_list

    def read_settings(self) -> StudySettings:
        study_settings = self._settings_service.read_study_settings()
        self._settings = study_settings
        return study_settings

    def update_settings(self, settings: StudySettingsUpdate) -> None:
        self._settings_service.edit_study_settings(settings)
        self._settings = self._settings_service.read_study_settings()

    def get_areas(self) -> MappingProxyType[str, Area]:
        return MappingProxyType(dict(sorted(self._areas.items())))

    def get_links(self) -> MappingProxyType[str, Link]:
        return MappingProxyType(self._links)

    def get_settings(self) -> StudySettings:
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
        temp_link = Link(area_from, area_to, link_service=cast(BaseLinkService, None))
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

    def delete_outputs(self) -> None:
        self._study_service.delete_outputs()
        self._outputs.clear()

    def delete_output(self, output_name: str) -> None:
        self._study_service.delete_output(output_name)
        self._outputs.pop(output_name)

    def move(self, parent_path: Path) -> None:
        self.path = self._study_service.move_study(parent_path)

    def generate_thermal_timeseries(self, nb_years: int) -> None:
        self._study_service.generate_thermal_timeseries(nb_years)
        self._settings.general_parameters.nb_timeseries_thermal = nb_years


# Design note:
# all following methods are entry points for study creation.
# They use methods defined in "local" and "API" implementation services,
# that we inject here.
# Generally speaking, implementations should reference the API, not the
# opposite. Here we perform dependency injection, and because of python
# import mechanics, we need to use local imports to avoid circular dependencies.


def create_study_local(study_name: str, version: str, parent_directory: "Path") -> "Study":
    from antares.craft.service.local_services.factory import create_study_local

    return create_study_local(study_name, version, parent_directory)


def read_study_local(study_path: "Path") -> "Study":
    from antares.craft.service.local_services.factory import read_study_local

    return read_study_local(study_path)


def create_study_api(
    study_name: str, version: str, api_config: APIconf, parent_path: "Optional[Path]" = None
) -> "Study":
    from antares.craft.service.api_services.factory import create_study_api

    return create_study_api(study_name, version, api_config, parent_path)


def import_study_api(api_config: APIconf, study_path: "Path", destination_path: "Optional[Path]" = None) -> "Study":
    from antares.craft.service.api_services.factory import import_study_api

    return import_study_api(api_config, study_path, destination_path)


def read_study_api(api_config: APIconf, study_id: str) -> "Study":
    from antares.craft.service.api_services.factory import read_study_api

    return read_study_api(api_config, study_id)


def create_variant_api(api_config: APIconf, study_id: str, variant_name: str) -> "Study":
    from antares.craft.service.api_services.factory import create_variant_api

    return create_variant_api(api_config, study_id, variant_name)
