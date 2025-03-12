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

from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path, PurePath
from typing import TYPE_CHECKING, Dict, Optional

import pandas as pd

from antares.craft.config.base_configuration import BaseConfiguration
from antares.craft.model.settings.study_settings import StudySettings, StudySettingsUpdate
from antares.craft.model.simulation import AntaresSimulationParameters, Job

if TYPE_CHECKING:
    from antares.craft.model.area import Area, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
    from antares.craft.model.binding_constraint import (
        BindingConstraint,
        BindingConstraintProperties,
        BindingConstraintPropertiesUpdate,
        ConstraintMatrixName,
        ConstraintTerm,
        ConstraintTermUpdate,
    )
    from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate
    from antares.craft.model.link import Link, LinkProperties, LinkPropertiesUpdate, LinkUi, LinkUiUpdate
    from antares.craft.model.output import AggregationEntry, Output
    from antares.craft.model.renewable import (
        RenewableCluster,
        RenewableClusterProperties,
        RenewableClusterPropertiesUpdate,
    )
    from antares.craft.model.st_storage import (
        STStorage,
        STStorageMatrixName,
        STStorageProperties,
        STStoragePropertiesUpdate,
    )
    from antares.craft.model.study import Study
    from antares.craft.model.thermal import (
        ThermalCluster,
        ThermalClusterMatrixName,
        ThermalClusterProperties,
        ThermalClusterPropertiesUpdate,
    )


class BaseAreaService(ABC):
    @property
    @abstractmethod
    def thermal_service(self) -> "BaseThermalService":
        pass

    @abstractmethod
    def create_area(
        self, area_name: str, properties: Optional["AreaProperties"] = None, ui: Optional["AreaUi"] = None
    ) -> "Area":
        pass

    @abstractmethod
    def create_thermal_cluster(
        self,
        area_id: str,
        cluster_name: str,
        properties: Optional["ThermalClusterProperties"] = None,
        prepro: Optional[pd.DataFrame] = None,
        modulation: Optional[pd.DataFrame] = None,
        series: Optional[pd.DataFrame] = None,
        co2_cost: Optional[pd.DataFrame] = None,
        fuel_cost: Optional[pd.DataFrame] = None,
    ) -> "ThermalCluster":
        """
        Args:

            area_id: area id in which to create the thermal cluster
            cluster_name: thermal cluster nam
            properties: properties of the thermal cluster.
            prepro: matrix corresponding to prepro/data.txt
            modulation: matrix corresponding to prepro/modulation.txt
            series: matrix for series/series.txt
            co2_cost: matrix for series/CO2Cost.txt
            fuel_cost: matrix for series/fuelCost.txt

        Returns:
           Thermal cluster created
        """
        pass

    @abstractmethod
    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional["RenewableClusterProperties"] = None,
        series: Optional[pd.DataFrame] = None,
    ) -> "RenewableCluster":
        """
        Args:
            area_id: the area id in which to create the renewable cluster
            renewable_name: the name of the renewable cluster
            properties: the properties of the renewable cluster. If not provided, AntaresWeb will use its own default values.
            series: matrix for renewables/area_id/renewable_name/series.txt

        Returns:
            The created renewable cluster
        """
        pass

    @abstractmethod
    def set_load(self, area_id: str, series: pd.DataFrame) -> None:
        """
        Args:
            area_id: area to create load series matrices
            series: load/series/load_{area_id}.txt

        """
        pass

    @abstractmethod
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional["STStorageProperties"] = None
    ) -> "STStorage":
        """
        Args:

            area_id: the area id in which to create the short term storage
            st_storage_name: the name of the short term storage
            properties: the properties of the short term storage. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created short term storage
        """
        pass

    @abstractmethod
    def set_wind(self, area_id: str, series: pd.DataFrame) -> None:
        """
        Args:
            area_id: area to create wind series matrices
            series: wind/series/wind_{area_id}.txt

        """
        pass

    @abstractmethod
    def set_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        """
        Args:
            area_id: str to create reserves series matrices
            series: Pandas dataframe stored in reserves/{area_id}.txt

        Returns:
            Reserves object with the provided Pandas dataframe
        """
        pass

    @abstractmethod
    def set_solar(self, area_id: str, series: pd.DataFrame) -> None:
        """
        Args:
            area_id: area to create reserves series matrices
            series: solar/series/solar_{area_id}.txt

        """
        pass

    @abstractmethod
    def set_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        """
        Args:
            area_id: area to create reserves series matrices
            series: misc-gen/miscgen-{area_id}.txt

        """
        pass

    @abstractmethod
    def update_area_properties(self, area_id: str, properties: "AreaPropertiesUpdate") -> "AreaProperties":
        """
        Args:
            area_id: concerned area
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def update_area_ui(self, area_id: str, ui: "AreaUiUpdate") -> "AreaUi":
        """
        Args:
            area_id: concerned area
            ui: new ui. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def delete_area(self, area_id: str) -> None:
        """
        Args:
            area: area object to be deleted
        """
        pass

    @abstractmethod
    def delete_thermal_clusters(self, area_id: str, thermal_clusters: list["ThermalCluster"]) -> None:
        """
        Args:
            area_id: area containing the cluster
            thermal_clusters: list of thermal clusters object to be deleted
        """
        pass

    @abstractmethod
    def delete_renewable_clusters(self, area_id: str, renewable_clusters: list["RenewableCluster"]) -> None:
        """
        Args:
            area_id: area containing the cluster
            renewable_clusters: list of renewable clusters object to be deleted
        """
        pass

    @abstractmethod
    def delete_st_storages(self, area_id: str, storages: list["STStorage"]) -> None:
        """
        Args:
            area_id: area containing the cluster
            storages: list of short term storage objects to be deleted
        """
        pass

    @abstractmethod
    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        """
        Args:
            area_id: concerned area.
        """
        # Currently we do not return index and column names.
        # Once AntaresWeb will introduce specific endpoint for each matrix it will perhaps change.
        # Same goes for other endpoints getting input matrices.
        pass

    @abstractmethod
    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        """
        Args:
            area_id: concerned area.
        """
        pass

    @abstractmethod
    def get_misc_gen_matrix(self, area_id: str) -> pd.DataFrame:
        """
        Args:
            area_id: concerned area.
        """
        pass

    @abstractmethod
    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        """
        Args:
            area_id: concerned area.
        """
        pass

    @abstractmethod
    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        """
        Args:
            area_id: concerned area.
        """
        pass

    @abstractmethod
    def read_areas(self) -> list["Area"]:
        """
        Returns: Returns a list of areas
        """
        pass

    @abstractmethod
    def update_multiple_areas(self, dict_areas: Dict[str, "AreaPropertiesUpdate"]) -> Dict[str, "AreaProperties"]:
        pass


class BaseHydroService(ABC):
    @abstractmethod
    def update_properties(self, area_id: str, properties: "HydroPropertiesUpdate") -> None:
        """
        Args:
            area_id: area in which hydro will be created
            properties: hydro properties
        """
        pass

    @abstractmethod
    def read_properties(self, area_id: str) -> "HydroProperties":
        """
        Args:
            area_id: area in which hydro will be created
        Returns:
            The hydro properties
        """
        pass

    @abstractmethod
    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_water_values(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_ror_series(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_mod_series(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_mingen(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def get_energy(self, area_id: str) -> pd.DataFrame:
        pass

    @abstractmethod
    def set_maxpower(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_reservoir(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_inflow_pattern(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_credits_modulation(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_water_values(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_ror_series(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_mod_series(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_mingen(self, area_id: str, series: pd.DataFrame) -> None:
        pass

    @abstractmethod
    def set_energy(self, area_id: str, series: pd.DataFrame) -> None:
        pass


class BaseLinkService(ABC):
    @abstractmethod
    def create_link(
        self,
        area_from: str,
        area_to: str,
        properties: Optional["LinkProperties"] = None,
        ui: Optional["LinkUi"] = None,
    ) -> "Link":
        """
        Args:
            area_from: area where the link goes from
            area_to: area where the link goes to
            properties: link's properties
            ui: link's ui characteristics

        Returns:
            The created link
        """
        pass

    @abstractmethod
    def delete_link(self, link: "Link") -> None:
        """
        Args:
            link: link object to be deleted
        """
        pass

    @abstractmethod
    def update_link_properties(self, link: "Link", properties: "LinkPropertiesUpdate") -> "LinkProperties":
        """
        Args:
            link: concerned link
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def update_link_ui(self, link: "Link", ui: "LinkUiUpdate") -> "LinkUi":
        """
        Args:
            link: concerned link
            ui: new ui. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_parameters(self, area_from: str, area_to: str) -> pd.DataFrame:
        """
        Returns: link parameters
        """
        pass

    @abstractmethod
    def set_parameters(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        pass

    @abstractmethod
    def read_links(self) -> list["Link"]:
        pass

    @abstractmethod
    def get_capacity_direct(self, area_from: str, area_to: str) -> pd.DataFrame:
        """
        Returns: the direct capacity of a link
        """
        pass

    @abstractmethod
    def set_capacity_direct(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        pass

    @abstractmethod
    def get_capacity_indirect(self, area_from: str, area_to: str) -> pd.DataFrame:
        """
        Returns: the indirect capacity of a link
        """
        pass

    @abstractmethod
    def set_capacity_indirect(self, series: pd.DataFrame, area_from: str, area_to: str) -> None:
        pass

    @abstractmethod
    def update_multiple_links(self, dict_links: Dict[str, "LinkPropertiesUpdate"]) -> Dict[str, "LinkProperties"]:
        pass


class BaseThermalService(ABC):
    @abstractmethod
    def update_thermal_properties(
        self, thermal_cluster: "ThermalCluster", properties: "ThermalClusterPropertiesUpdate"
    ) -> "ThermalClusterProperties":
        """
        Args:
            thermal_cluster: concerned cluster
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def set_thermal_matrix(
        self, thermal_cluster: "ThermalCluster", matrix: pd.DataFrame, ts_name: "ThermalClusterMatrixName"
    ) -> None:
        pass

    @abstractmethod
    def get_thermal_matrix(
        self, thermal_cluster: "ThermalCluster", ts_name: "ThermalClusterMatrixName"
    ) -> pd.DataFrame:
        """
        Args:
            thermal_cluster: cluster to retrieve matrix
            ts_name:  matrix name

        Returns: matrix requested

        """
        pass

    @abstractmethod
    def read_thermal_clusters(self, area_id: str) -> list["ThermalCluster"]:
        pass

    @abstractmethod
    def update_multiple_thermal_clusters(
        self, new_properties: dict["ThermalCluster", "ThermalClusterPropertiesUpdate"]
    ) -> dict["ThermalCluster", "ThermalClusterProperties"]:
        pass


class BaseBindingConstraintService(ABC):
    @abstractmethod
    def create_binding_constraint(
        self,
        name: str,
        properties: Optional["BindingConstraintProperties"] = None,
        terms: Optional[list["ConstraintTerm"]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> "BindingConstraint":
        """
        Args:
            name: the binding constraint name
            properties: the properties of the constraint. If not provided, AntaresWeb will use its own default values.
            terms: the terms of the constraint. If not provided, no term will be created.
            less_term_matrix: matrix corresponding to the lower bound of the constraint. If not provided, no matrix will be created.
            equal_term_matrix: matrix corresponding to the equality bound of the constraint. If not provided, no matrix will be created.
            greater_term_matrix: matrix corresponding to the upper bound of the constraint. If not provided, no matrix will be created.

        Returns:
            The created binding constraint
        """
        pass

    @abstractmethod
    def add_constraint_terms(self, constraint: "BindingConstraint", terms: list["ConstraintTerm"]) -> None:
        """
        Args:
            constraint: the concerned binding constraint
            terms: the terms to add to the constraint.

        Returns:
            The created terms
        """
        pass

    @abstractmethod
    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        """
        Args:
            constraint_id: binding constraint's id containing the term
            term_id: binding constraint term to be deleted
        """
        pass

    @abstractmethod
    def update_binding_constraint_term(
        self, constraint_id: str, term: "ConstraintTermUpdate", existing_term: "ConstraintTerm"
    ) -> "ConstraintTerm":
        """
        Args:
            constraint_id: binding constraint's id containing the term
            term: term with new values
            existing_term: existing term with existing values
        """
        pass

    @abstractmethod
    def update_binding_constraint_properties(
        self, binding_constraint: "BindingConstraint", properties: "BindingConstraintPropertiesUpdate"
    ) -> "BindingConstraintProperties":
        """
        Args:
            binding_constraint: concerned binding_constraint
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_constraint_matrix(
        self, constraint: "BindingConstraint", matrix_name: "ConstraintMatrixName"
    ) -> pd.DataFrame:
        """
        Args:
            constraint: the concerned binding constraint
            matrix_name: the matrix suffix.
        """
        pass

    @abstractmethod
    def set_constraint_matrix(
        self, constraint: "BindingConstraint", matrix_name: "ConstraintMatrixName", matrix: pd.DataFrame
    ) -> None:
        """
        Args:
            constraint: the concerned binding constraint
            matrix_name: the matrix suffix.
            matrix: matrix to upload (in Dataframe format)
        """
        pass

    @abstractmethod
    def read_binding_constraints(self) -> list["BindingConstraint"]:
        """
        Loads binding constraints into study

        Returns: the list of binding constraints that have been fetched
        """
        pass

    @abstractmethod
    def update_multiple_binding_constraints(
        self, new_properties: Dict[str, "BindingConstraintPropertiesUpdate"]
    ) -> Dict[str, "BindingConstraintProperties"]:
        pass


class BaseStudyService(ABC):
    @property
    @abstractmethod
    def study_id(self) -> str:
        """The ID for the study"""
        pass

    @property
    @abstractmethod
    def config(self) -> BaseConfiguration:
        """The configuration of the study."""
        pass

    @abstractmethod
    def delete_binding_constraint(self, constraint: "BindingConstraint") -> None:
        """
        Args:
            constraint: binding constraint object to be deleted
        """
        pass

    @abstractmethod
    def delete(self, children: bool) -> None:
        """
        Deletes the study and its children if children is True
        """
        pass

    @abstractmethod
    def create_variant(self, variant_name: str) -> "Study":
        """
        Creates a new variant for the study

        Args:
            variant_name: the name of the new variant
        Returns: the variant
        """
        pass

    @abstractmethod
    def move_study(self, new_parent_path: Path) -> PurePath:
        """
        Moves the study to the new parent path

        Returns: the new path
        """
        pass

    @abstractmethod
    def read_outputs(self) -> list["Output"]:
        """
        Gets the output list of a study

        Returns: "Output" list
        """
        pass

    @abstractmethod
    def delete_outputs(self) -> None:
        """
        Deletes all the outputs of the study
        """
        pass

    @abstractmethod
    def delete_output(self, output_name: str) -> None:
        """
        Deletes given output from the study

        Args:
            output_name: To be deleted output
        """
        pass

    @abstractmethod
    def generate_thermal_timeseries(self, number_of_years: int, areas: dict[str, "Area"], seed: int) -> None:
        pass


class BaseRenewableService(ABC):
    @abstractmethod
    def update_renewable_properties(
        self, renewable_cluster: "RenewableCluster", properties: "RenewableClusterPropertiesUpdate"
    ) -> "RenewableClusterProperties":
        """
        Args:
            renewable_cluster: concerned cluster
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_renewable_matrix(self, cluster_id: str, area_id: str) -> pd.DataFrame:
        """
        Args:
            cluster_id: renewable cluster id to retrieve matrix
            area_id: area id to retrieve matrix
        Returns: matrix requested

        """
        pass

    @abstractmethod
    def set_series(self, renewable_cluster: "RenewableCluster", matrix: pd.DataFrame) -> None:
        """
        Args:
            renewable_cluster: the renewable_cluster
            matrix: the renewable matrix we want to update
        Returns: None
        """
        pass

    @abstractmethod
    def read_renewables(self, area_id: str) -> list["RenewableCluster"]:
        pass


class BaseShortTermStorageService(ABC):
    @abstractmethod
    def update_st_storage_properties(
        self, st_storage: "STStorage", properties: "STStoragePropertiesUpdate"
    ) -> "STStorageProperties":
        """
        Args:
            st_storage: concerned storage
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def read_st_storages(self, area_id: str) -> list["STStorage"]:
        pass

    @abstractmethod
    def get_storage_matrix(self, storage: "STStorage", ts_name: "STStorageMatrixName") -> pd.DataFrame:
        pass

    @abstractmethod
    def set_storage_matrix(self, storage: "STStorage", ts_name: "STStorageMatrixName", matrix: pd.DataFrame) -> None:
        pass


class BaseRunService(ABC):
    @abstractmethod
    def run_antares_simulation(
        self, parameters: Optional[AntaresSimulationParameters] = None, solver_path: Optional[Path] = None
    ) -> Job:
        """
        Runs the Antares simulation.

        This method starts an antares simulation for the current study config and params

        Returns: A job representing the simulation task
        """
        pass

    @abstractmethod
    def wait_job_completion(self, job: Job, time_out: int) -> None:
        """
        Waits for the completion of a job

        Args:
            job: The job to wait for
            time_out: Time limit for waiting (seconds)

        Raises: SimulationTimeOutError if exceeded timeout
        """
        pass


class BaseOutputService(ABC):
    @abstractmethod
    def get_matrix(self, output_id: str, file_path: str) -> pd.DataFrame:
        """
        Gets the matrix of the output

        Args:
            output_id: id of the output
            file_path: output path

        Returns: Pandas DataFrame
        """
        pass

    @abstractmethod
    def aggregate_values(
        self, output_id: str, aggregation_entry: "AggregationEntry", object_type: str, mc_type: str
    ) -> pd.DataFrame:
        """
        Creates a matrix of aggregated raw data

        Args:
            output_id: id of the output
            aggregation_entry: input (query_file, frequency, mc_years, ..)
            mc_type: all or ind (enum)
            object_type: links or areas (enum)

        Returns: Pandas DataFrame corresponding to the aggregated raw data
        """
        pass


class BaseStudySettingsService(ABC):
    @abstractmethod
    def edit_study_settings(self, settings: StudySettingsUpdate) -> None:
        """
        Edit the settings for a given study

        Args:
            settings: the settings to update with their values
        """
        pass

    @abstractmethod
    def read_study_settings(self) -> StudySettings:
        """
        Reads the settings of a study
        """
        pass


@dataclass(frozen=True)
class StudyServices:
    settings_service: BaseStudySettingsService
    study_service: BaseStudyService
    area_service: BaseAreaService
    link_service: BaseLinkService
    thermal_service: BaseThermalService
    hydro_service: BaseHydroService
    bc_service: BaseBindingConstraintService
    renewable_service: BaseRenewableService
    short_term_storage_service: BaseShortTermStorageService
    run_service: BaseRunService
    output_service: BaseOutputService
