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
from typing import Any, Optional

import pandas as pd

from antares.craft.model.commons import FilterOption
from antares.craft.model.hydro import Hydro, HydroProperties
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
from pydantic import BaseModel, computed_field
from pydantic.alias_generators import to_camel


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


def default_filtering() -> set[FilterOption]:
    return {
        FilterOption.HOURLY,
        FilterOption.DAILY,
        FilterOption.WEEKLY,
        FilterOption.MONTHLY,
        FilterOption.ANNUAL,
    }


@dataclass
class AreaProperties:
    energy_cost_unsupplied: float = 0.0
    energy_cost_spilled: float = 0.0
    non_dispatch_power: bool = True
    dispatch_hydro_power: bool = True
    other_dispatch_power: bool = True
    filter_synthesis: set[FilterOption] = field(default_factory=default_filtering)
    filter_by_year: set[FilterOption] = field(default_factory=default_filtering)
    adequacy_patch_mode: AdequacyPatchMode = AdequacyPatchMode.OUTSIDE
    spread_unsupplied_energy_cost: float = 0.0
    spread_spilled_energy_cost: float = 0.0


class AreaUi(BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel):
    """
    DTO for updating area UI
    """

    # TODO: What do these fields mean ?

    layer: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    color_rgb: Optional[list[int]] = None

    layer_x: Optional[dict[int, int]] = None
    layer_y: Optional[dict[int, int]] = None
    layer_color: Optional[dict[int, str]] = None


class AreaUiLocal(BaseModel):
    """
    DTO for updating area UI locally in the ini files
    """

    def __init__(
        self,
        input_area_ui: AreaUi = AreaUi(),
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        self._x = input_area_ui.x or 0
        self._y = input_area_ui.y or 0
        self._color_r, self._color_g, self._color_b = input_area_ui.color_rgb or [230, 108, 44]
        self._layers = input_area_ui.layer or 0
        self._layer_x = input_area_ui.layer_x or {self._layers: self._x}
        self._layer_y = input_area_ui.layer_y or {self._layers: self._y}
        self._layer_color = input_area_ui.layer_color or {
            self._layers: f"{self._color_r} , {self._color_g} , {self._color_b}"
        }

    @computed_field  # type: ignore[misc]
    @property
    def ui(self) -> dict[str, Optional[int]]:
        return dict(
            x=self._x,
            y=self._y,
            color_r=self._color_r,
            color_g=self._color_g,
            color_b=self._color_b,
            layers=self._layers,
        )

    @computed_field  # type: ignore[misc]
    @property
    def layerX(self) -> dict[int, int]:
        return self._layer_x

    @computed_field  # type: ignore[misc]
    @property
    def layerY(self) -> dict[int, int]:
        return self._layer_y

    @computed_field  # type: ignore[misc]
    @property
    def layerColor(self) -> dict[int, str]:
        return self._layer_color

    def yield_area_ui(self) -> AreaUi:
        return AreaUi(
            layer=self._layers,
            x=self._x,
            y=self._y,
            color_rgb=[self._color_r, self._color_g, self._color_b],
            layer_x=self._layer_x,
            layer_y=self._layer_y,
            layer_color=self._layer_color,
        )


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
        self._renewables = renewables or dict()
        self._thermals = thermals or dict()
        self._st_storages = st_storages or dict()
        self._hydro = hydro or Hydro(self._hydro_service, self._id, HydroProperties())
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
        self,
        thermal_name: str,
        properties: Optional[ThermalClusterProperties] = None,
        prepro: Optional[pd.DataFrame] = None,
        modulation: Optional[pd.DataFrame] = None,
        series: Optional[pd.DataFrame] = None,
        co2_cost: Optional[pd.DataFrame] = None,
        fuel_cost: Optional[pd.DataFrame] = None,
    ) -> ThermalCluster:
        thermal = self._area_service.create_thermal_cluster(
            self.id, thermal_name, properties, prepro, modulation, series, co2_cost, fuel_cost
        )
        self._thermals[thermal.id] = thermal
        return thermal

    def create_renewable_cluster(
        self, renewable_name: str, properties: Optional[RenewableClusterProperties], series: Optional[pd.DataFrame]
    ) -> RenewableCluster:
        renewable = self._area_service.create_renewable_cluster(self.id, renewable_name, properties, series=series)
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
        self._area_service.delete_thermal_clusters(self.id, thermal_clusters)
        for cluster in thermal_clusters:
            self._thermals.pop(cluster.id)

    def delete_thermal_cluster(self, thermal_cluster: ThermalCluster) -> None:
        self.delete_thermal_clusters([thermal_cluster])

    def delete_renewable_clusters(self, renewable_clusters: list[RenewableCluster]) -> None:
        self._area_service.delete_renewable_clusters(self.id, renewable_clusters)
        for cluster in renewable_clusters:
            self._renewables.pop(cluster.id)

    def delete_renewable_cluster(self, renewable_cluster: RenewableCluster) -> None:
        self.delete_renewable_clusters([renewable_cluster])

    def delete_st_storages(self, storages: list[STStorage]) -> None:
        self._area_service.delete_st_storages(self.id, storages)
        for storage in storages:
            self._st_storages.pop(storage.id)

    def delete_st_storage(self, storage: STStorage) -> None:
        self.delete_st_storages([storage])

    def update_properties(self, properties: AreaPropertiesUpdate) -> None:
        new_properties = self._area_service.update_area_properties(self.id, properties)
        self._properties = new_properties

    def update_ui(self, ui: AreaUi) -> None:
        new_ui = self._area_service.update_area_ui(self.id, ui)
        self._ui = new_ui

    def create_load(self, series: pd.DataFrame) -> None:
        self._area_service.create_load(self.id, series)

    def create_wind(self, series: pd.DataFrame) -> None:
        self._area_service.create_wind(self.id, series)

    def create_reserves(self, series: pd.DataFrame) -> None:
        self._area_service.create_reserves(self.id, series)

    def create_solar(self, series: pd.DataFrame) -> None:
        self._area_service.create_solar(self.id, series)

    def create_misc_gen(self, series: pd.DataFrame) -> None:
        self._area_service.create_misc_gen(self.id, series)

    def read_st_storages(
        self,
    ) -> list[STStorage]:
        return self._storage_service.read_st_storages(self.id)

    def read_renewables(
        self,
    ) -> list[RenewableCluster]:
        return self._renewable_service.read_renewables(self.id)

    def read_thermal_clusters(
        self,
    ) -> list[ThermalCluster]:
        return self._thermal_service.read_thermal_clusters(self.id)
