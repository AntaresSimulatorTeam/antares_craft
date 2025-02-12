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
from antares.craft.model.area import (
    Area,
    AreaProperties,
    AreaPropertiesLocal,
    AreaUi,
    AreaUiLocal,
)
from antares.craft.model.hydro import Hydro, HydroMatrixName, HydroProperties
from antares.craft.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.craft.model.st_storage import STStorage, STStorageProperties, STStoragePropertiesLocal
from antares.craft.model.thermal import ThermalCluster, ThermalClusterProperties
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseHydroService,
    BaseRenewableService,
    BaseShortTermStorageService,
    BaseThermalService,
)
from antares.craft.service.local_services.models.renewable import RenewableClusterPropertiesLocal
from antares.craft.service.local_services.models.thermal import ThermalClusterPropertiesLocal
from antares.craft.service.local_services.services.hydro import edit_hydro_properties, read_hydro_properties
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
from antares.craft.tools.prepro_folder import PreproFolder
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


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
    def __init__(
        self,
        config: LocalConfiguration,
        study_name: str,
        storage_service: BaseShortTermStorageService,
        thermal_service: BaseThermalService,
        renewable_service: BaseRenewableService,
        hydro_service: BaseHydroService,
        **kwargs: Any,
    ) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.storage_service: BaseShortTermStorageService = storage_service
        self.thermal_service: BaseThermalService = thermal_service
        self.renewable_service: BaseRenewableService = renewable_service
        self.hydro_service: BaseHydroService = hydro_service

    @override
    def create_thermal_cluster(
        self,
        area_id: str,
        thermal_name: str,
        properties: Optional[ThermalClusterProperties] = None,
        prepro: Optional[pd.DataFrame] = None,
        modulation: Optional[pd.DataFrame] = None,
        series: Optional[pd.DataFrame] = None,
        co2_cost: Optional[pd.DataFrame] = None,
        fuel_cost: Optional[pd.DataFrame] = None,
    ) -> ThermalCluster:
        # Creating files
        list_ini = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_LIST_INI, area_id=area_id)
        IniFile(
            self.config.study_path,
            InitializationFilesTypes.THERMAL_MODULATION,
            area_id=area_id,
            cluster_id=thermal_name,
        )
        IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_DATA, area_id=area_id, cluster_id=thermal_name)
        IniFile(
            self.config.study_path, InitializationFilesTypes.THERMAL_SERIES, area_id=area_id, cluster_id=thermal_name
        )

        # Writing properties
        try:
            properties = properties or ThermalClusterProperties()
            local_properties = ThermalClusterPropertiesLocal.from_user_model(properties)
            new_section_content = {"name": thermal_name, **local_properties.model_dump(mode="json", by_alias=True)}
            list_ini.add_section({thermal_name: new_section_content})
        except DuplicateSectionError:
            raise ThermalCreationError(
                thermal_name,
                area_id,
                f"A thermal cluster called '{thermal_name}' already exists in area '{area_id}'.",
            )
        list_ini.write_ini_file(sort_sections=True)

        # Upload matrices
        if prepro:
            self._write_timeseries(prepro, TimeSeriesFileType.THERMAL_DATA, area_id)
        if modulation:
            self._write_timeseries(modulation, TimeSeriesFileType.THERMAL_MODULATION, area_id)
        if series:
            self._write_timeseries(series, TimeSeriesFileType.THERMAL_SERIES, area_id)
        if co2_cost:
            self._write_timeseries(co2_cost, TimeSeriesFileType.THERMAL_CO2, area_id)
        if fuel_cost:
            self._write_timeseries(fuel_cost, TimeSeriesFileType.THERMAL_FUEL, area_id)

        return ThermalCluster(self.thermal_service, area_id, thermal_name, properties)

    @override
    def create_renewable_cluster(
        self,
        area_id: str,
        renewable_name: str,
        properties: Optional[RenewableClusterProperties] = None,
        series: Optional[pd.DataFrame] = None,
    ) -> RenewableCluster:
        properties = properties or RenewableClusterProperties()
        local_properties = RenewableClusterPropertiesLocal.from_user_model(properties)
        new_section_content = {"name": renewable_name, **local_properties.model_dump(mode="json", by_alias=True)}

        list_ini = IniFile(self.config.study_path, InitializationFilesTypes.RENEWABLES_LIST_INI, area_id=area_id)
        list_ini.add_section({renewable_name: new_section_content})
        list_ini.write_ini_file()

        if series:
            self._write_timeseries(series, TimeSeriesFileType.RENEWABLE_DATA_SERIES, area_id)

        return RenewableCluster(self.renewable_service, area_id, renewable_name, properties)

    @override
    def create_load(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.LOAD, area_id)
        PreproFolder.LOAD.save(self.config.study_path, area_id)

    def _write_timeseries(self, series: pd.DataFrame, ts_file_type: TimeSeriesFileType, area_id: str) -> None:
        file_path = self.config.study_path.joinpath(ts_file_type.value.format(area_id=area_id))
        series.to_csv(file_path, sep="\t", header=False, index=False, encoding="utf-8")

    @override
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        properties = properties or STStorageProperties()
        args = {"st_storage_name": st_storage_name, **properties.model_dump(mode="json", exclude_none=True)}
        local_st_storage_properties = STStoragePropertiesLocal.model_validate(args)

        list_ini = IniFile(self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id)
        list_ini.add_section(local_st_storage_properties.list_ini_fields)
        list_ini.write_ini_file(sort_sections=True)

        return STStorage(
            self.storage_service,
            area_id,
            st_storage_name,
            local_st_storage_properties.yield_st_storage_properties(),
        )

    @override
    def create_wind(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.WIND, area_id)
        PreproFolder.WIND.save(self.config.study_path, area_id)

    @override
    def create_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.RESERVES, area_id)

    @override
    def create_solar(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.SOLAR, area_id)
        PreproFolder.SOLAR.save(self.config.study_path, area_id)

    @override
    def create_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        self._write_timeseries(series, TimeSeriesFileType.MISC_GEN, area_id)

    @override
    def create_hydro(
        self,
        area_id: str,
        properties: Optional[HydroProperties] = None,
        matrices: Optional[Dict[HydroMatrixName, pd.DataFrame]] = None,
    ) -> Hydro:
        properties = properties or HydroProperties()
        update_properties = properties.to_update_properties()
        edit_hydro_properties(self.config.study_path, area_id, update_properties, creation=True)
        return Hydro(self.hydro_service, area_id, properties)

    @override
    def read_hydro(
        self,
        area_id: str,
    ) -> Hydro:
        hydro_properties = read_hydro_properties(self.config.study_path, area_id)
        return Hydro(self.hydro_service, area_id, hydro_properties)

    @override
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

            with (self.config.study_path / InitializationFilesTypes.AREAS_SETS_INI.value).open("w") as sets_ini:
                sets_ini_content.write(sets_ini)

            local_properties = (
                AreaPropertiesLocal.model_validate(properties.model_dump(mode="json", exclude_none=True))
                if properties
                else AreaPropertiesLocal()
            )

            adequacy_patch_ini = IniFile(
                self.config.study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area_name
            )
            adequacy_patch_ini.add_section(local_properties.adequacy_patch())
            adequacy_patch_ini.write_ini_file()

            optimization_ini = ConfigParser()
            optimization_ini.read_dict(local_properties.yield_local_dict())

            with open(new_area_directory / "optimization.ini", "w") as optimization_ini_file:
                optimization_ini.write(optimization_ini_file)

            areas_ini = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_AREAS_INI)
            if not areas_ini.ini_dict:
                areas_ini.add_section({"unserverdenergycost": {}})
                areas_ini.add_section({"spilledenergycost": {}})
                areas_ini.write_ini_file()

            areas_ini.parsed_ini["unserverdenergycost"][area_name] = str(local_properties.energy_cost_unsupplied)
            areas_ini.parsed_ini["spilledenergycost"][area_name] = str(local_properties.energy_cost_spilled)
            areas_ini.write_ini_file()

            local_ui = AreaUiLocal(ui) if ui else AreaUiLocal()
            ui_ini = ConfigParser()
            ui_ini.read_dict(local_ui.model_dump(exclude_none=True))
            with open(new_area_directory / "ui.ini", "w") as ui_ini_file:
                ui_ini.write(ui_ini_file)

            empty_df = pd.DataFrame()
            self.create_reserves(area_name, empty_df)
            self.create_misc_gen(area_name, empty_df)
            self.create_load(area_name, empty_df)
            self.create_solar(area_name, empty_df)
            self.create_wind(area_name, empty_df)
            IniFile.create_link_ini_for_area(self.config.study_path, area_name)
            IniFile.create_list_ini_for_area(self.config.study_path, area_name)

        except Exception as e:
            raise AreaCreationError(area_name, f"{e}") from e

        logging.info(f"Area {area_name} created successfully!")
        area_id = transform_name_to_id(area_name)
        default_hydro_properties = HydroProperties()
        update_properties = default_hydro_properties.to_update_properties()
        edit_hydro_properties(self.config.study_path, area_id, update_properties, creation=True)
        hydro = Hydro(self.hydro_service, area_id, default_hydro_properties)
        created_area = Area(
            name=area_name,
            area_service=self,
            storage_service=self.storage_service,
            thermal_service=self.thermal_service,
            renewable_service=self.renewable_service,
            hydro_service=self.hydro_service,
            hydro=hydro,
            properties=local_properties.yield_area_properties(),
            ui=local_ui.yield_area_ui(),
        )
        return created_area

    @override
    def delete_area(self, area_id: str) -> None:
        raise NotImplementedError

    @override
    def update_area_properties(self, area_id: str, properties: AreaProperties) -> AreaProperties:
        raise NotImplementedError

    @override
    def update_area_ui(self, area_id: str, ui: AreaUi) -> AreaUi:
        raise NotImplementedError

    @override
    def delete_thermal_clusters(self, area_id: str, thermal_clusters: List[ThermalCluster]) -> None:
        raise NotImplementedError

    @override
    def delete_renewable_clusters(self, area_id: str, renewable_clusters: List[RenewableCluster]) -> None:
        raise NotImplementedError

    @override
    def delete_st_storages(self, area_id: str, storages: List[STStorage]) -> None:
        raise NotImplementedError

    @override
    def get_load_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.LOAD, self.config.study_path, area_id=area_id)

    @override
    def get_solar_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.SOLAR, self.config.study_path, area_id=area_id)

    @override
    def get_wind_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.WIND, self.config.study_path, area_id=area_id)

    @override
    def get_reserves_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.RESERVES, self.config.study_path, area_id=area_id)

    @override
    def get_misc_gen_matrix(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.MISC_GEN, self.config.study_path, area_id=area_id)

    @override
    def read_areas(self) -> List[Area]:
        local_path = self.config.local_path
        areas_path = local_path / self.study_name / "input" / "areas"
        areas = []
        for element in areas_path.iterdir():
            if element.is_dir():
                optimization_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_OPTIMIZATION_INI, area_id=element.name
                ).ini_dict
                area_adequacy_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area_id=element.name
                ).ini_dict
                ui_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_UI_INI, area_id=element.name
                ).ini_dict
                thermal_area_dict = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_AREAS_INI).ini_dict
                nodal_optimization = optimization_dict["nodal optimization"]
                area_properties = AreaPropertiesLocal(
                    non_dispatch_power=nodal_optimization.get("non-dispatchable-power"),
                    dispatch_hydro_power=nodal_optimization.get("dispatchable-hydro-power"),
                    other_dispatch_power=nodal_optimization.get("other-dispatchable-power"),
                    spread_unsupplied_energy_cost=nodal_optimization.get("spread-unsupplied-energy-cost"),
                    spread_spilled_energy_cost=nodal_optimization.get("spread-spilled-energy-cost"),
                    energy_cost_unsupplied=thermal_area_dict["unserverdenergycost"].get(element.name),
                    energy_cost_spilled=thermal_area_dict["spilledenergycost"].get(element.name),
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
                area_id = transform_name_to_id(element.name)
                hydro = self.read_hydro(area_id)
                area = Area(
                    name=element.name,
                    area_service=self,
                    storage_service=self.storage_service,
                    thermal_service=self.thermal_service,
                    renewable_service=self.renewable_service,
                    hydro_service=self.hydro_service,
                    properties=area_properties.yield_area_properties(),
                    ui=ui_properties,
                    hydro=hydro,
                )
                areas.append(area)

        areas.sort(key=lambda area_obj: area_obj.id)
        return areas
