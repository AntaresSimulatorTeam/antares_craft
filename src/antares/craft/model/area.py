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

"""
The Area model defines the description of the
electrical demand (load), generation fleet (clusters),
//TO_DO to be completed as implementation progress
"""

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Optional

import pandas as pd

from antares.craft.exceptions.exceptions import RenewableDeletionError, STStorageDeletionError, ThermalDeletionError
from antares.craft.model.commons import FILTER_VALUES, FilterOption
from antares.craft.model.hydro import Hydro, HydroProperties, InflowStructure
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage, STStorageProperties
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseHydroService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.tools.contents_tool import EnumIgnoreCase, transform_name_to_id

DELETION_ERROR_MSG = "it doesn't exist"


class AdequacyPatchMode(EnumIgnoreCase):
    """
    Adequacy patch mode.

    Only available if study version >= 830.
    """

    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


@dataclass
class AreaPropertiesUpdate:
    energy_cost_unsupplied: Optional[float] = None
    energy_cost_spilled: Optional[float] = None
    non_dispatch_power: Optional[bool] = None
    dispatch_hydro_power: Optional[bool] = None
    other_dispatch_power: Optional[bool] = None
    filter_synthesis: Optional[set[FilterOption]] = None
    filter_by_year: Optional[set[FilterOption]] = None
    adequacy_patch_mode: Optional[AdequacyPatchMode] = None
    spread_unsupplied_energy_cost: Optional[float] = None
    spread_spilled_energy_cost: Optional[float] = None


@dataclass(frozen=True)
class AreaProperties:
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0
    non_dispatch_power: bool = True
    dispatch_hydro_power: bool = True
    other_dispatch_power: bool = True
    filter_synthesis: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    filter_by_year: set[FilterOption] = field(default_factory=lambda: FILTER_VALUES)
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0


@dataclass
class AreaUiUpdate:
    x: Optional[int] = None
    y: Optional[int] = None
    color_rgb: Optional[list[int]] = None

    def __post_init__(self) -> None:
        if self.color_rgb and len(self.color_rgb) != 3:
            raise ValueError(f"The `color_rgb` list must contain exactly 3 values, currently {self.color_rgb}")


@dataclass(frozen=True)
class AreaUi:
    x: int = 0
    y: int = 0
    color_rgb: list[int] = field(default_factory=lambda: [230, 108, 44])

    def __post_init__(self) -> None:
        if len(self.color_rgb) != 3:
            raise ValueError(f"The `color_rgb` list must contain exactly 3 values, currently {self.color_rgb}")


class Area:
    def __init__(
        self,
        name: str,
        area_service: BaseAreaService,
        storage_service: BaseShortTermStorageService,
        thermal_service: BaseThermalService,
        renewable_service: BaseRenewableService,
        hydro_service: BaseHydroService,
        *,
        renewables: Optional[dict[str, RenewableCluster]] = None,
        thermals: Optional[dict[str, ThermalCluster]] = None,
        st_storages: Optional[dict[str, STStorage]] = None,
        hydro: Optional[Hydro] = None,
        properties: Optional[AreaProperties] = None,
        ui: Optional[AreaUi] = None,
    ):
        self._name = name
        self._id = transform_name_to_id(name)
        self._area_service = area_service
        self._storage_service = storage_service
        self._thermal_service = thermal_service
        self._renewable_service = renewable_service
        self._hydro_service = hydro_service
        self._renewables = renewables or {}
        self._thermals = thermals or {}
        self._st_storages = st_storages or {}
        self._hydro = hydro or Hydro(self._hydro_service, self._id, HydroProperties(), InflowStructure())
        self._properties = properties or AreaProperties()
        self._ui = ui or AreaUi()

    @property
    def name(self) -> str:
        return self._name

    @property
    def id(self) -> str:
        return self._id

    def get_thermals(self) -> MappingProxyType[str, ThermalCluster]:
        return MappingProxyType(self._thermals)

    def get_renewables(self) -> MappingProxyType[str, RenewableCluster]:
        return MappingProxyType(self._renewables)

    def get_st_storages(self) -> MappingProxyType[str, STStorage]:
        return MappingProxyType(self._st_storages)

    @property
    def hydro(self) -> Hydro:
        return self._hydro

    @property
    def properties(self) -> AreaProperties:
        return self._properties

    @property
    def ui(self) -> AreaUi:
        return self._ui

    def create_thermal_cluster(
        self, thermal_name: str, properties: Optional[ThermalClusterProperties] = None
    ) -> ThermalCluster:
        thermal = self._area_service.create_thermal_cluster(self.id, thermal_name, properties)
        self._thermals[thermal.id] = thermal
        return thermal

    def create_renewable_cluster(
        self, renewable_name: str, properties: Optional[RenewableClusterProperties] = None
    ) -> RenewableCluster:
        renewable = self._area_service.create_renewable_cluster(self.id, renewable_name, properties)
        self._renewables[renewable.id] = renewable
        return renewable

    def create_st_storage(self, st_storage_name: str, properties: Optional[STStorageProperties] = None) -> STStorage:
        storage = self._area_service.create_st_storage(self.id, st_storage_name, properties)
        self._st_storages[storage.id] = storage

        return storage

    def get_load_matrix(self) -> pd.DataFrame:
        return self._area_service.get_load_matrix(self.id)

    def get_wind_matrix(self) -> pd.DataFrame:
        return self._area_service.get_wind_matrix(self.id)

    def get_solar_matrix(self) -> pd.DataFrame:
        return self._area_service.get_solar_matrix(self.id)

    def get_reserves_matrix(self) -> pd.DataFrame:
        return self._area_service.get_reserves_matrix(self.id)

    def get_misc_gen_matrix(self) -> pd.DataFrame:
        return self._area_service.get_misc_gen_matrix(self.id)

    def delete_thermal_clusters(self, thermal_clusters: list[ThermalCluster]) -> None:
        # Checks deletion is possible
        bad_cluster_ids = []
        for cluster in thermal_clusters:
            if cluster.id not in self._thermals:
                bad_cluster_ids.append(cluster.id)
        if bad_cluster_ids:
            raise ThermalDeletionError(self.id, bad_cluster_ids, DELETION_ERROR_MSG)
        # Performs deletion
        self._area_service.delete_thermal_clusters(self.id, thermal_clusters)
        for cluster in thermal_clusters:
            self._thermals.pop(cluster.id)

    def delete_thermal_cluster(self, thermal_cluster: ThermalCluster) -> None:
        self.delete_thermal_clusters([thermal_cluster])

    def delete_renewable_clusters(self, renewable_clusters: list[RenewableCluster]) -> None:
        # Checks deletion is possible
        bad_cluster_ids = []
        for cluster in renewable_clusters:
            if cluster.id not in self._renewables:
                bad_cluster_ids.append(cluster.id)
        if bad_cluster_ids:
            raise RenewableDeletionError(self.id, bad_cluster_ids, DELETION_ERROR_MSG)
        # Performs deletion
        self._area_service.delete_renewable_clusters(self.id, renewable_clusters)
        for cluster in renewable_clusters:
            self._renewables.pop(cluster.id)

    def delete_renewable_cluster(self, renewable_cluster: RenewableCluster) -> None:
        self.delete_renewable_clusters([renewable_cluster])

    def delete_st_storages(self, storages: list[STStorage]) -> None:
        # Checks deletion is possible
        bad_cluster_ids = []
        for cluster in storages:
            if cluster.id not in self._st_storages:
                bad_cluster_ids.append(cluster.id)
        if bad_cluster_ids:
            raise STStorageDeletionError(self.id, bad_cluster_ids, DELETION_ERROR_MSG)
        # Performs deletion
        self._area_service.delete_st_storages(self.id, storages)
        for storage in storages:
            self._st_storages.pop(storage.id)

    def delete_st_storage(self, storage: STStorage) -> None:
        self.delete_st_storages([storage])

    def update_properties(self, properties: AreaPropertiesUpdate) -> AreaProperties:
        new_properties = self._area_service.update_areas_properties({self: properties})
        self._properties = new_properties[self.id]
        return self._properties

    def update_ui(self, ui: AreaUiUpdate) -> AreaUi:
        new_ui = self._area_service.update_area_ui(self, ui)
        self._ui = new_ui
        return new_ui

    def set_load(self, series: pd.DataFrame) -> None:
        self._area_service.set_load(self.id, series)

    def set_wind(self, series: pd.DataFrame) -> None:
        self._area_service.set_wind(self.id, series)

    def set_reserves(self, series: pd.DataFrame) -> None:
        self._area_service.set_reserves(self.id, series)

    def set_solar(self, series: pd.DataFrame) -> None:
        self._area_service.set_solar(self.id, series)

    def set_misc_gen(self, series: pd.DataFrame) -> None:
        self._area_service.set_misc_gen(self.id, series)
