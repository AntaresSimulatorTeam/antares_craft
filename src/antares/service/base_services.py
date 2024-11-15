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
from types import MappingProxyType
from typing import Dict, List, Optional

import pandas as pd

from antares.config.base_configuration import BaseConfiguration
from antares.model.area import Area, AreaProperties, AreaUi
from antares.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintProperties,
    ConstraintMatrixName,
    ConstraintTerm,
)
from antares.model.hydro import Hydro, HydroMatrixName, HydroProperties
from antares.model.link import Link, LinkProperties, LinkUi
from antares.model.load import Load
from antares.model.misc_gen import MiscGen
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.model.reserves import Reserves
from antares.model.settings.study_settings import StudySettings
from antares.model.solar import Solar
from antares.model.st_storage import STStorage, STStorageProperties
from antares.model.thermal import ThermalCluster, ThermalClusterMatrixName, ThermalClusterProperties
from antares.model.wind import Wind


class BaseAreaService(ABC):
    @abstractmethod
    def set_storage_service(self, storage_service: "BaseShortTermStorageService") -> None:
        pass

    @abstractmethod
    def set_thermal_service(self, thermal_service: "BaseThermalService") -> None:
        pass

    @abstractmethod
    def set_renewable_service(self, renewable_service: "BaseRenewableService") -> None:
        pass

    @abstractmethod
    def create_area(
        self, area_name: str, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        pass

    @abstractmethod
    def create_thermal_cluster(
        self, area_id: str, thermal_name: str, properties: Optional[ThermalClusterProperties] = None
    ) -> ThermalCluster:
        """
        Args:
            area_id: the area id in which to create the thermal cluster
            thermal_name: the name of the thermal cluster
            properties: the properties of the thermal cluster. If not provided, AntaresWeb will use its own default values.

        Returns:
            The created thermal cluster
        """
        pass

    @abstractmethod
    def read_areas(self) -> List[Area]:
        """
        Returns: Returns a list of areas
        """
        pass

    @abstractmethod
    def create_thermal_cluster_with_matrices(
        self,
        area_id: str,
        cluster_name: str,
        parameters: ThermalClusterProperties,
        prepro: Optional[pd.DataFrame],
        modulation: Optional[pd.DataFrame],
        series: Optional[pd.DataFrame],
        CO2Cost: Optional[pd.DataFrame],
        fuelCost: Optional[pd.DataFrame],
    ) -> ThermalCluster:
        """

        Args:

            area_id: area id in which to create the thermal cluster
            cluster_name: thermal cluster nam
            parameters: properties of the thermal cluster.
            prepro: matrix corresponding to prepro/data.txt
            modulation: matrix corresponding to prepro/modulation.txt
            series: matrix for series/series.txt
            CO2Cost: matrix for series/CO2Cost.txt
            fuelCost: matrix for series/fuelCost.txt

        Returns:
           Thermal cluster created
        """
        pass

    @abstractmethod
    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties],
        series: Optional[pd.DataFrame],
    ) -> RenewableCluster:
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
    def create_load(self, area: Area, series: Optional[pd.DataFrame]) -> Load:
        """
        Args:
            area: area to create load series matrices
            series: load/series/load_{area_id}.txt

        """
        pass

    @abstractmethod
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
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
    def create_wind(self, area: Area, series: Optional[pd.DataFrame]) -> Wind:
        """
        Args:
            area: area to create wind series matrices
            series: wind/series/wind_{area_id}.txt

        """
        pass

    @abstractmethod
    def create_reserves(self, area: Area, series: Optional[pd.DataFrame]) -> Reserves:
        """
        Args:
            area: Area to create reserves series matrices
            series: Pandas dataframe stored in reserves/{area_id}.txt

        Returns:
            Reserves object with the provided Pandas dataframe
        """
        pass

    @abstractmethod
    def create_solar(self, area: Area, series: Optional[pd.DataFrame]) -> Solar:
        """
        Args:
            area: area to create reserves series matrices
            series: solar/series/solar_{area_id}.txt

        """
        pass

    @abstractmethod
    def create_misc_gen(self, area: Area, series: Optional[pd.DataFrame]) -> MiscGen:
        """
        Args:
            area: area to create reserves series matrices
            series: misc-gen/miscgen-{area_id}.txt

        """
        pass

    @abstractmethod
    def create_hydro(
        self,
        area_id: str,
        properties: Optional[HydroProperties],
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]],
    ) -> Hydro:
        """
        Args:
            area_id: area in which hydro will be created
            properties: hydro properties
            matrices: matrices for hydro to be created

        """
        pass

    @abstractmethod
    def update_area_properties(self, area: Area, properties: AreaProperties) -> AreaProperties:
        """
        Args:
            area: concerned area
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def update_area_ui(self, area: Area, ui: AreaUi) -> AreaUi:
        """
        Args:
            area: concerned area
            ui: new ui. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def delete_area(self, area: Area) -> None:
        """
        Args:
            area: area object to be deleted
        """
        pass

    @abstractmethod
    def delete_thermal_clusters(self, area: Area, thermal_clusters: List[ThermalCluster]) -> None:
        """
        Args:
            area: area containing the cluster
            thermal_clusters: List of thermal clusters object to be deleted
        """
        pass

    @abstractmethod
    def delete_renewable_clusters(self, area: Area, renewable_clusters: List[RenewableCluster]) -> None:
        """
        Args:
            area: area containing the cluster
            renewable_clusters: List of renewable clusters object to be deleted
        """
        pass

    @abstractmethod
    def delete_st_storages(self, area: Area, storages: List[STStorage]) -> None:
        """
        Args:
            area: area containing the cluster
            storages: List of short term storage objects to be deleted
        """
        pass

    @abstractmethod
    def upload_load_matrix(self, area: Area, load_matrix: pd.DataFrame) -> None:
        """
        Args:
            area: concerned area.
            load_matrix: matrix in Dataframe format to write as the load matrix.
        """
        # todo: What happens when given an empty DataFrame ? AntaresWeb doesn't handle such a case.
        pass

    @abstractmethod
    def get_load_matrix(self, area: Area) -> pd.DataFrame:
        """
        Args:
            area: concerned area.
        """
        # todo: Currently we do not return index and column names because AntaresWeb doesn't send the full information.
        # Once it will, there will be no change to do in the code on our side.
        pass


class BaseLinkService(ABC):
    @abstractmethod
    def create_link(
        self,
        area_from: Area,
        area_to: Area,
        properties: Optional[LinkProperties] = None,
        ui: Optional[LinkUi] = None,
        existing_areas: Optional[MappingProxyType[str, Area]] = None,
    ) -> Link:
        """
        Args:
            area_from: area where the link goes from
            area_to: area where the link goes to
            properties: link's properties
            ui: link's ui characteristics
            existing_areas: existing areas from study

        Returns:
            The created link
        """
        pass

    @abstractmethod
    def delete_link(self, link: Link) -> None:
        """
        Args:
            link: link object to be deleted
        """
        pass

    @abstractmethod
    def update_link_properties(self, link: Link, properties: LinkProperties) -> LinkProperties:
        """
        Args:
            link: concerned link
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def update_link_ui(self, link: Link, ui: LinkUi) -> LinkUi:
        """
        Args:
            link: concerned link
            ui: new ui. Only registered fields will be updated.
        """
        pass


class BaseThermalService(ABC):
    @abstractmethod
    def update_thermal_properties(
        self, thermal_cluster: ThermalCluster, properties: ThermalClusterProperties
    ) -> ThermalClusterProperties:
        """
        Args:
            thermal_cluster: concerned cluster
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_thermal_matrix(self, thermal_cluster: ThermalCluster, ts_name: ThermalClusterMatrixName) -> pd.DataFrame:
        """
        Args:
            thermal_cluster: cluster to retrieve matrix
            ts_name:  matrix name

        Returns: matrix requested

        """
        pass


class BaseBindingConstraintService(ABC):
    binding_constraints: dict[str, BindingConstraint]

    @abstractmethod
    def create_binding_constraint(
        self,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[List[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
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
    def add_constraint_terms(self, constraint: BindingConstraint, terms: List[ConstraintTerm]) -> List[ConstraintTerm]:
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
    def update_binding_constraint_properties(
        self, binding_constraint: BindingConstraint, properties: BindingConstraintProperties
    ) -> BindingConstraintProperties:
        """
        Args:
            binding_constraint: concerned binding_constraint
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        """
        Args:
            constraint: the concerned binding constraint
            matrix_name: the matrix suffix.
        """
        pass

    @abstractmethod
    def update_constraint_matrix(
        self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName, matrix: pd.DataFrame
    ) -> None:
        """
        Args:
            constraint: the concerned binding constraint
            matrix_name: the matrix suffix.
            matrix: matrix to upload (in Dataframe format)
        """
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
    def update_study_settings(self, settings: StudySettings) -> Optional[StudySettings]:
        """
        Args:
            settings: new study settings. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
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


class BaseRenewableService(ABC):
    @abstractmethod
    def update_renewable_properties(
        self, renewable_cluster: RenewableCluster, properties: RenewableClusterProperties
    ) -> RenewableClusterProperties:
        """
        Args:
            renewable_cluster: concerned cluster
            properties: new properties. Only registered fields will be updated.
        """
        pass

    @abstractmethod
    def get_renewable_matrix(
        self,
        renewable: RenewableCluster,
    ) -> pd.DataFrame:
        """
        Args:
            renewable: renewable cluster to retrieve matrix

        Returns: matrix requested

        """
        pass


class BaseShortTermStorageService(ABC):
    @abstractmethod
    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStorageProperties
    ) -> STStorageProperties:
        """
        Args:
            st_storage: concerned storage
            properties: new properties. Only registered fields will be updated.
        """
        pass
