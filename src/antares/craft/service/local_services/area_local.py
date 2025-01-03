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

from configparser import ConfigParser, DuplicateSectionError
from typing import Any, Dict, List, Optional

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import AreaCreationError, ThermalCreationError
from antares.craft.model.area import Area, AreaProperties, AreaPropertiesLocal, AreaUi, AreaUiLocal
from antares.craft.model.hydro import Hydro, HydroMatrixName, HydroProperties, HydroPropertiesLocal
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties, RenewableClusterPropertiesLocal
from antares.craft.model.st_storage import STStorage, STStorageProperties, STStoragePropertiesLocal
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties, ThermalClusterPropertiesLocal
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.prepro_folder import PreproFolder
from antares.craft.tools.time_series_tool import TimeSeriesFileType


def _sets_ini_content() -> ConfigParser:
    """
    Returns: sets.ini contents with default values
    """
    sets_ini = ConfigParser()
    sets_ini_dict = {
        "all areas": {
            "caption": "All areas",
            "comments": "Spatial aggregates on all areas",
            "output": "false",
            "apply-filter": "add-all",
        }
    }
    sets_ini.read_dict(sets_ini_dict)
    return sets_ini


class AreaLocalService(BaseAreaService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def set_storage_service(self, storage_service: BaseShortTermStorageService) -> None:
        self.storage_service = storage_service

    def set_thermal_service(self, thermal_service: BaseThermalService) -> None:
        self.thermal_service = thermal_service

    def set_renewable_service(self, renewable_service: BaseRenewableService) -> None:
        self.renewable_service = renewable_service

    def create_thermal_cluster(
        self,
        area_id: str,
        thermal_name: str,
        properties: Optional[ThermalClusterProperties] = None,
    ) -> ThermalCluster:
        properties = properties or ThermalClusterProperties()
        args = {"thermal_name": thermal_name, **properties.model_dump(mode="json", exclude_none=True)}
        local_thermal_properties = ThermalClusterPropertiesLocal.model_validate(args)

        list_ini = IniFile(self.config.study_path, IniFileTypes.THERMAL_LIST_INI, area_id=area_id)
        try:
            list_ini.add_section(local_thermal_properties.list_ini_fields)
        except DuplicateSectionError:
            raise ThermalCreationError(
                thermal_name,
                area_id,
                f"A thermal cluster called '{thermal_name}' already exists in area '{area_id}'.",
            )
        list_ini.write_ini_file(sort_sections=True)

        return ThermalCluster(
            self.thermal_service, area_id, thermal_name, local_thermal_properties.yield_thermal_cluster_properties()
        )

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
        raise NotImplementedError

    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties] = None,
        series: Optional[pd.DataFrame] = None,
    ) -> RenewableCluster:
        properties = properties or RenewableClusterProperties()
        args = {"renewable_name": renewable_name, **properties.model_dump(mode="json", exclude_none=True)}
        local_properties = RenewableClusterPropertiesLocal.model_validate(args)

        list_ini = IniFile(self.config.study_path, IniFileTypes.RENEWABLES_LIST_INI, area_id=area_id)
        list_ini.add_section(local_properties.ini_fields)
        list_ini.write_ini_file()

        return RenewableCluster(
            self.renewable_service, area_id, renewable_name, local_properties.yield_renewable_cluster_properties()
        )

    def create_load(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.LOAD, area_id)
        PreproFolder.LOAD.save(self.config.study_path, area_id)

    def _write_timeseries(self, series: pd.DataFrame, ts_file_type: TimeSeriesFileType, area_id: str) -> None:
        file_path = self.config.study_path.joinpath(ts_file_type.value.format(area_id=area_id))
        series.to_csv(file_path, sep="\t", header=False, index=False, encoding="utf-8")

    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        properties = properties or STStorageProperties()
        args = {"st_storage_name": st_storage_name, **properties.model_dump(mode="json", exclude_none=True)}
        local_st_storage_properties = STStoragePropertiesLocal.model_validate(args)

        list_ini = IniFile(self.config.study_path, IniFileTypes.ST_STORAGE_LIST_INI, area_id=area_id)
        list_ini.add_section(local_st_storage_properties.list_ini_fields)
        list_ini.write_ini_file(sort_sections=True)

        return STStorage(
            self.storage_service,
            area_id,
            st_storage_name,
            local_st_storage_properties.yield_st_storage_properties(),
        )

    def create_wind(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.WIND, area_id)
        PreproFolder.WIND.save(self.config.study_path, area_id)

    def create_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.RESERVES, area_id)

    def create_solar(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.SOLAR, area_id)
        PreproFolder.SOLAR.save(self.config.study_path, area_id)

    def create_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.MISC_GEN, area_id)

    def create_hydro(
        self,
        area_id: str,
        properties: Optional[HydroProperties] = None,
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]] = None,
    ) -> Hydro:
        properties = properties or HydroProperties()
        args = {"area_id": area_id, **properties.model_dump(mode="json", exclude_none=True)}
        local_hydro_properties = HydroPropertiesLocal.model_validate(args)

        list_ini = IniFile(self.config.study_path, IniFileTypes.HYDRO_INI)
        list_ini.add_section(local_hydro_properties.hydro_ini_fields, append=True)
        list_ini.write_ini_file(sort_section_content=True)

        return Hydro(self, area_id, local_hydro_properties.yield_hydro_properties())

    def read_hydro(
        self,
        area_id: str,
    ) -> Hydro:
        raise NotImplementedError

    def create_area(
        self, area_name: str, properties: Optional[AreaProperties] = None, ui: Optional[AreaUi] = None
    ) -> Area:
        """
        Args:
            area_name: area to be added to study
            properties: area's properties. If not provided, default values will be used.
            ui: area's ui characteristics. If not provided, default values will be used.

        Returns: area name if success or Error if area can not be
        created
        """

        def _line_exists_in_file(file_content: str, line_to_add: str) -> bool:
            """
            Args:
                file_content: file content to check
                line_to_add: line to add

            Returns: True if line is already present in file.

            """
            return line_to_add.strip() in file_content.split("\n")

        study_directory = self.config.local_path.joinpath(self.study_name, "input")
        areas_directory = study_directory.joinpath("areas")
        new_area_directory = areas_directory.joinpath(transform_name_to_id(area_name))

        if new_area_directory.is_dir():
            raise AreaCreationError(
                area_name, f"There is already an area '{area_name}' in the study '{self.study_name}'"
            )

        # Create "areas" directory if it doesn't exist
        os.makedirs(new_area_directory, exist_ok=True)

        list_path = areas_directory.joinpath("list.txt")

        area_to_add = f"{area_name}\n"
        try:
            if os.path.isfile(list_path):
                with open(list_path, "r") as list_file:
                    list_file_content = list_file.read()
                if _line_exists_in_file(list_file_content, area_to_add):
                    raise ValueError(f"The Area '{area_name}' already exists in the study {self.study_name}.")
                updated_list = sorted(list_file_content.splitlines(keepends=True) + [area_to_add])
            else:
                updated_list = [area_to_add]

            # Write area(s) to file list.txt
            with open(list_path, "w") as list_txt:
                list_txt.write("".join(map(str, updated_list)))

            # TODO: Handle districts in sets.ini later
            sets_ini_content = _sets_ini_content()

            with (self.config.study_path / IniFileTypes.AREAS_SETS_INI.value).open("w") as sets_ini:
                sets_ini_content.write(sets_ini)

            local_properties = (
                AreaPropertiesLocal.model_validate(properties.model_dump(mode="json", exclude_none=True))
                if properties
                else AreaPropertiesLocal()
            )

            adequacy_patch_ini = IniFile(self.config.study_path, IniFileTypes.AREA_ADEQUACY_PATCH_INI, area_name)
            adequacy_patch_ini.add_section(local_properties.adequacy_patch())
            adequacy_patch_ini.write_ini_file()

            optimization_ini = ConfigParser()
            optimization_ini.read_dict(local_properties.yield_local_dict())

            with open(new_area_directory / "optimization.ini", "w") as optimization_ini_file:
                optimization_ini.write(optimization_ini_file)

            areas_ini = IniFile(self.config.study_path, IniFileTypes.THERMAL_AREAS_INI)
            if not areas_ini.ini_dict:
                areas_ini.add_section({"unserverdenergycost": {}})
                areas_ini.add_section({"spilledenergycost": {}})
                areas_ini.write_ini_file()
            areas_ini.parsed_ini["unserverdenergycost"][area_name] = local_properties.nodal_optimization[
                "average-unsupplied-energy-cost"
            ]
            areas_ini.parsed_ini["spilledenergycost"][area_name] = local_properties.nodal_optimization[
                "average-spilled-energy-cost"
            ]
            areas_ini.write_ini_file()

            local_ui = AreaUiLocal(ui) if ui else AreaUiLocal()
            ui_ini = ConfigParser()
            ui_ini.read_dict(local_ui.model_dump(exclude_none=True))
            with open(new_area_directory / "ui.ini", "w") as ui_ini_file:
                ui_ini.write(ui_ini_file)

        except Exception as e:
            raise AreaCreationError(area_name, f"{e}") from e

        logging.info(f"Area {area_name} created successfully!")
        created_area = Area(
            name=area_name,
            area_service=self,
            storage_service=self.storage_service,
            thermal_service=self.thermal_service,
            renewable_service=self.renewable_service,
            properties=local_properties.yield_area_properties(),
            ui=local_ui.yield_area_ui(),
        )
        created_area.create_hydro()
        return created_area

    def delete_area(self, area_id: str) -> None:
        raise NotImplementedError

    def update_area_properties(self, area_id: str, properties: AreaProperties) -> AreaProperties:
        raise NotImplementedError

    def update_area_ui(self, area_id: str, ui: AreaUi) -> AreaUi:
        raise NotImplementedError

    def delete_thermal_clusters(self, area_id: str, thermal_clusters: List[ThermalCluster]) -> None:
        raise NotImplementedError

    def delete_renewable_clusters(self, area_id: str, renewable_clusters: List[RenewableCluster]) -> None:
        raise NotImplementedError

    def delete_st_storages(self, area_id: str, storages: List[STStorage]) -> None:
        raise NotImplementedError

    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.LOAD, self.config.study_path, area_id=area_id)

    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.SOLAR, self.config.study_path, area_id=area_id)

    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.WIND, self.config.study_path, area_id=area_id)

    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.RESERVES, self.config.study_path, area_id=area_id)

    def get_misc_gen_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.MISC_GEN, self.config.study_path, area_id=area_id)

    def read_areas(self) -> List[Area]:
        local_path = self.config.local_path
        areas_path = local_path / self.study_name / "input" / "areas"
        areas = []
        for element in areas_path.iterdir():
            if element.is_dir():
                optimization_dict = IniFile(
                    self.config.study_path, IniFileTypes.AREA_OPTIMIZATION_INI, area_id=element.name
                ).ini_dict
                area_adequacy_dict = IniFile(
                    self.config.study_path, IniFileTypes.AREA_ADEQUACY_PATCH_INI, area_id=element.name
                ).ini_dict
                ui_dict = IniFile(self.config.study_path, IniFileTypes.AREA_UI_INI, area_id=element.name).ini_dict
                area_properties = AreaPropertiesLocal(
                    non_dispatch_power=optimization_dict["nodal optimization"].get("non-dispatchable-power"),
                    dispatch_hydro_power=optimization_dict["nodal optimization"].get("dispatchable-hydro-power"),
                    other_dispatch_power=optimization_dict["nodal optimization"].get("other-dispatchable-power"),
                    spread_unsupplied_energy_cost=optimization_dict["nodal optimization"].get(
                        "spread-unsupplied-energy-cost"
                    ),
                    spread_spilled_energy_cost=optimization_dict["nodal optimization"].get(
                        "spread-spilled-energy-cost"
                    ),
                    energy_cost_unsupplied=optimization_dict["nodal optimization"].get(
                        "average-unsupplied-energy-cost"
                    ),
                    energy_cost_spilled=optimization_dict["nodal optimization"].get("average-spilled-energy-cost"),
                    filter_synthesis=set(optimization_dict["filtering"].get("filter-synthesis").split(", ")),
                    filter_by_year=set(optimization_dict["filtering"].get("filter-year-by-year").split(", ")),
                    adequacy_patch_mode=area_adequacy_dict["adequacy-patch"].get("adequacy-patch-mode"),
                )
                ui_properties = AreaUi(
                    layer=ui_dict["ui"].get("layer"),
                    x=ui_dict["ui"].get("x"),
                    y=ui_dict["ui"].get("y"),
                    color_rgb=[
                        ui_dict["ui"].get("color_r", 0),
                        ui_dict["ui"].get("color_g", 0),
                        ui_dict["ui"].get("color_b", 0),
                    ],
                    layer_x=ui_dict["ui"].get("layerX"),
                    layer_y=ui_dict["ui"].get("layerY"),
                    layer_color=ui_dict["ui"].get("layerColor"),
                )
                areas.append(
                    Area(
                        name=element.name,
                        area_service=self,
                        storage_service=self.storage_service,
                        thermal_service=self.thermal_service,
                        renewable_service=self.renewable_service,
                        properties=area_properties.yield_area_properties(),
                        ui=ui_properties,
                    )
                )
        return areas
