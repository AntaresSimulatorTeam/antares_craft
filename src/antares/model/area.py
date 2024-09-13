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

from types import MappingProxyType
from typing import Optional, Dict, List, Any, Mapping, Set

import pandas as pd
from pydantic import BaseModel, computed_field
from pydantic.alias_generators import to_camel

from antares.model.commons import FilterOption, sort_filter_values
from antares.model.hydro import HydroProperties, HydroMatrixName, Hydro
from antares.model.misc_gen import MiscGen
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.model.reserves import Reserves
from antares.model.solar import Solar
from antares.model.st_storage import STStorage, STStorageProperties
from antares.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.model.wind import Wind
from antares.tools.contents_tool import transform_name_to_id, EnumIgnoreCase


class AdequacyPatchMode(EnumIgnoreCase):
    """
    Adequacy patch mode.

    Only available if study version >= 830.
    """

    OUTSIDE = "outside"
    INSIDE = "inside"
    VIRTUAL = "virtual"


# todo: Warning, with filesystem, we want to avoid camel case and use link_aliasing.
class AreaProperties(
    BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel
):
    """
    DTO for updating area properties
    """

    energy_cost_unsupplied: Optional[float] = None
    energy_cost_spilled: Optional[float] = None
    non_dispatch_power: Optional[bool] = None
    dispatch_hydro_power: Optional[bool] = None
    other_dispatch_power: Optional[bool] = None
    filter_synthesis: Optional[Set[FilterOption]] = None
    filter_by_year: Optional[Set[FilterOption]] = None
    # version 830
    adequacy_patch_mode: Optional[AdequacyPatchMode] = None
    spread_unsupplied_energy_cost: Optional[float] = None
    spread_spilled_energy_cost: Optional[float] = None


def config_alias_generator(field_name: str) -> str:
    return field_name.replace("_", " ")


# TODO update to use check_if_none
class AreaPropertiesLocal(BaseModel, alias_generator=config_alias_generator):
    def __init__(
        self,
        input_area_properties: AreaProperties = AreaProperties(),
        **kwargs: Optional[Any],
    ):
        super().__init__(**kwargs)
        self._energy_cost_unsupplied = (
            input_area_properties.energy_cost_unsupplied or 0.0
        )
        self._energy_cost_spilled = input_area_properties.energy_cost_spilled or 0.0
        self._non_dispatch_power = (
            input_area_properties.non_dispatch_power
            if input_area_properties.non_dispatch_power is not None
            else True
        )
        self._dispatch_hydro_power = (
            input_area_properties.dispatch_hydro_power
            if input_area_properties.dispatch_hydro_power is not None
            else True
        )
        self._other_dispatch_power = (
            input_area_properties.other_dispatch_power
            if input_area_properties.other_dispatch_power is not None
            else True
        )
        self._filter_synthesis = input_area_properties.filter_synthesis or {
            FilterOption.HOURLY,
            FilterOption.DAILY,
            FilterOption.WEEKLY,
            FilterOption.MONTHLY,
            FilterOption.ANNUAL,
        }
        self._filter_by_year = input_area_properties.filter_by_year or {
            FilterOption.HOURLY,
            FilterOption.DAILY,
            FilterOption.WEEKLY,
            FilterOption.MONTHLY,
            FilterOption.ANNUAL,
        }
        self._adequacy_patch_mode = (
            input_area_properties.adequacy_patch_mode
            if input_area_properties.adequacy_patch_mode
            else AdequacyPatchMode.OUTSIDE
        )
        self._spread_spilled_energy_cost = (
            input_area_properties.spread_spilled_energy_cost or 0.0
        )
        self._spread_unsupplied_energy_cost = (
            input_area_properties.spread_unsupplied_energy_cost or 0.0
        )

    @computed_field  # type: ignore[misc]
    @property
    def nodal_optimization(self) -> Mapping[str, str]:
        return {
            "non-dispatchable-power": f"{self._non_dispatch_power}".lower(),
            "dispatchable-hydro-power": f"{self._dispatch_hydro_power}".lower(),
            "other-dispatchable-power": f"{self._other_dispatch_power}".lower(),
            "spread-unsupplied-energy-cost": f"{self._spread_unsupplied_energy_cost:.6f}",
            "spread-spilled-energy-cost": f"{self._spread_spilled_energy_cost:.6f}",
            "average-unsupplied-energy-cost": f"{self._energy_cost_unsupplied:.6f}",
            "average-spilled-energy-cost": f"{self._energy_cost_spilled:.6f}",
        }

    @computed_field  # type: ignore[misc]
    @property
    def filtering(self) -> Mapping[str, str]:
        return {
            "filter-synthesis": ", ".join(
                filter_value
                for filter_value in sort_filter_values(self._filter_synthesis)
            ),
            "filter-year-by-year": ", ".join(
                filter_value
                for filter_value in sort_filter_values(self._filter_by_year)
            ),
        }

    def adequacy_patch_mode(self) -> dict[str, dict[str, str]]:
        return {
            "adequacy-patch": {"adequacy-patch-mode": self._adequacy_patch_mode.value}
        }

    def yield_area_properties(self) -> AreaProperties:
        return AreaProperties(
            energy_cost_unsupplied=self._energy_cost_unsupplied,
            energy_cost_spilled=self._energy_cost_spilled,
            non_dispatch_power=self._non_dispatch_power,
            dispatch_hydro_power=self._dispatch_hydro_power,
            other_dispatch_power=self._other_dispatch_power,
            filter_synthesis=self._filter_synthesis,
            filter_by_year=self._filter_by_year,
            adequacy_patch_mode=self._adequacy_patch_mode,
            spread_unsupplied_energy_cost=self._spread_unsupplied_energy_cost,
            spread_spilled_energy_cost=self._spread_spilled_energy_cost,
        )


class AreaUi(
    BaseModel, extra="forbid", populate_by_name=True, alias_generator=to_camel
):
    """
    DTO for updating area UI
    """

    # TODO: What do these fields mean ?

    layer: Optional[int] = None
    x: Optional[int] = None
    y: Optional[int] = None
    color_rgb: Optional[List[int]] = None

    layer_x: Optional[Dict[int, int]] = None
    layer_y: Optional[Dict[int, int]] = None
    layer_color: Optional[Dict[int, str]] = None


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
        self._color_r, self._color_g, self._color_b = input_area_ui.color_rgb or [
            230,
            108,
            44,
        ]
        self._layers = input_area_ui.layer or 0
        self._layer_x = input_area_ui.layer_x or {self._layers: self._x}
        self._layer_y = input_area_ui.layer_y or {self._layers: self._y}
        self._layer_color = input_area_ui.layer_color or {
            self._layers: f"{self._color_r} , {self._color_g} , {self._color_b}"
        }

    @computed_field  # type: ignore[misc]
    @property
    def ui(self) -> Dict[str, Optional[int]]:
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
    def layerX(self) -> Dict[int, int]:
        return self._layer_x

    @computed_field  # type: ignore[misc]
    @property
    def layerY(self) -> Dict[int, int]:
        return self._layer_y

    @computed_field  # type: ignore[misc]
    @property
    def layerColor(self) -> Dict[int, str]:
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
    def __init__(  # type: ignore # TODO: Find a way to avoid circular imports
        self,
        name: str,
        area_service,
        storage_service,
        thermal_service,
        renewable_service,
        *,
        renewables: Optional[Dict[str, RenewableCluster]] = None,
        thermals: Optional[Dict[str, ThermalCluster]] = None,
        st_storages: Optional[Dict[str, STStorage]] = None,
        hydro: Optional[Hydro] = None,
        wind: Optional[Wind] = None,
        reserves: Optional[Reserves] = None,
        solar: Optional[Solar] = None,
        misc_gen: Optional[MiscGen] = None,
        properties: Optional[AreaProperties] = None,
        ui: Optional[AreaUi] = None,
    ):
        self._name = name
        self._id = transform_name_to_id(name)
        self._area_service = area_service
        self._storage_service = storage_service
        self._thermal_service = thermal_service
        self._renewable_service = renewable_service
        self._renewables = renewables or dict()
        self._thermals = thermals or dict()
        self._st_storages = st_storages or dict()
        self._hydro = hydro
        self._wind = wind
        self._reserves = reserves
        self._solar = solar
        self._misc_gen = misc_gen
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
    def hydro(self) -> Optional[Hydro]:
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
        thermal = self._area_service.create_thermal_cluster(
            self.id, thermal_name, properties
        )
        self._thermals[thermal.id] = thermal
        return thermal

    def create_thermal_cluster_with_matrices(
        self,
        cluster_name: str,
        parameters: ThermalClusterProperties,
        prepro: Optional[pd.DataFrame],
        modulation: Optional[pd.DataFrame],
        series: Optional[pd.DataFrame],
        CO2Cost: Optional[pd.DataFrame],
        fuelCost: Optional[pd.DataFrame],
    ) -> ThermalCluster:
        thermal = self._area_service.create_thermal_cluster_with_matrices(
            self.id,
            cluster_name,
            parameters,
            prepro,
            modulation,
            series,
            CO2Cost,
            fuelCost,
        )
        self._thermals[thermal.id] = thermal
        return thermal

    def create_renewable_cluster(
        self,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties],
        series: Optional[pd.DataFrame],
    ) -> RenewableCluster:
        renewable = self._area_service.create_renewable_cluster(
            self.id, renewable_name, properties, series
        )
        self._renewables[renewable.id] = renewable
        return renewable

    def create_st_storage(
        self, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        storage = self._area_service.create_st_storage(
            self.id, st_storage_name, properties
        )
        self._st_storages[storage.id] = storage

        return storage

    def get_load_matrix(self) -> pd.DataFrame:
        return self._area_service.get_load_matrix(self)

    def upload_load_matrix(self, load_matrix: pd.DataFrame) -> None:
        self._area_service.upload_load_matrix(self, load_matrix)

    def delete_thermal_clusters(self, thermal_clusters: List[ThermalCluster]) -> None:
        self._area_service.delete_thermal_clusters(self, thermal_clusters)
        for cluster in thermal_clusters:
            self._thermals.pop(cluster.id)

    def delete_thermal_cluster(self, thermal_cluster: ThermalCluster) -> None:
        self.delete_thermal_clusters([thermal_cluster])

    def delete_renewable_clusters(
        self, renewable_clusters: List[RenewableCluster]
    ) -> None:
        self._area_service.delete_renewable_clusters(self, renewable_clusters)
        for cluster in renewable_clusters:
            self._renewables.pop(cluster.id)

    def delete_renewable_cluster(self, renewable_cluster: RenewableCluster) -> None:
        self.delete_renewable_clusters([renewable_cluster])

    def delete_st_storages(self, storages: List[STStorage]) -> None:
        self._area_service.delete_st_storages(self, storages)
        for storage in storages:
            self._st_storages.pop(storage.id)

    def delete_st_storage(self, storage: STStorage) -> None:
        self.delete_st_storages([storage])

    def update_properties(self, properties: AreaProperties) -> None:
        new_properties = self._area_service.update_area_properties(self, properties)
        self._properties = new_properties

    def update_ui(self, ui: AreaUi) -> None:
        new_ui = self._area_service.update_area_ui(self, ui)
        self._ui = new_ui

    def create_wind(self, series: Optional[pd.DataFrame]) -> Wind:
        wind = self._area_service.create_wind(self, series)
        self._wind = wind
        return wind

    def create_reserves(self, series: Optional[pd.DataFrame]) -> Reserves:
        reserves = self._area_service.create_reserves(self, series)
        self._reserves = reserves
        return reserves

    def create_solar(self, series: Optional[pd.DataFrame]) -> Solar:
        solar = self._area_service.create_solar(self, series)
        self._solar = solar
        return solar

    def create_misc_gen(self, series: Optional[pd.DataFrame]) -> MiscGen:
        misc_gen = self._area_service.create_misc_gen(self, series)
        self._misc_gen = misc_gen
        return misc_gen

    def create_hydro(
        self,
        properties: Optional[HydroProperties] = None,
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]] = None,
    ) -> Hydro:
        # todo: is it necessary to create allocation or correlation ?
        hydro = self._area_service.create_hydro(self.id, properties, matrices)
        self._hydro = hydro
        return hydro
