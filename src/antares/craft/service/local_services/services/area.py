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
import copy
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
    AreaPropertiesUpdate,
    AreaUi,
    AreaUiUpdate,
)
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
from antares.craft.service.local_services.models.area import AreaPropertiesLocal, AreaUiLocal
from antares.craft.service.local_services.models.renewable import RenewableClusterPropertiesLocal
from antares.craft.service.local_services.models.st_storage import STStoragePropertiesLocal
from antares.craft.service.local_services.models.thermal import ThermalClusterPropertiesLocal
from antares.craft.service.local_services.services.hydro import edit_hydro_properties
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
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
        self._thermal_service: BaseThermalService = thermal_service
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
        cluster_id = transform_name_to_id(thermal_name)

        write_timeseries(self.config.study_path, prepro, TimeSeriesFileType.THERMAL_DATA, area_id, cluster_id)
        write_timeseries(self.config.study_path, modulation, TimeSeriesFileType.THERMAL_MODULATION, area_id, cluster_id)
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.THERMAL_SERIES, area_id, cluster_id)
        write_timeseries(self.config.study_path, co2_cost, TimeSeriesFileType.THERMAL_CO2, area_id, cluster_id)
        write_timeseries(self.config.study_path, fuel_cost, TimeSeriesFileType.THERMAL_FUEL, area_id, cluster_id)

        return ThermalCluster(self.thermal_service, area_id, thermal_name, properties)

    @override
    @property
    def thermal_service(self) -> "BaseThermalService":
        return self._thermal_service

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
        write_timeseries(
            self.config.study_path,
            series,
            TimeSeriesFileType.RENEWABLE_SERIES,
            area_id,
            cluster_id=transform_name_to_id(renewable_name),
        )
        return RenewableCluster(self.renewable_service, area_id, renewable_name, properties)

    @override
    def set_load(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.LOAD, area_id)
        PreproFolder.LOAD.save(self.config.study_path, area_id)

    @override
    def create_st_storage(
        self, area_id: str, st_storage_name: str, properties: Optional[STStorageProperties] = None
    ) -> STStorage:
        properties = properties or STStorageProperties()
        local_properties = STStoragePropertiesLocal.from_user_model(properties)
        new_section_content = {"name": st_storage_name, **local_properties.model_dump(mode="json", by_alias=True)}

        list_ini = IniFile(self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id)
        list_ini.add_section({st_storage_name: new_section_content})
        list_ini.write_ini_file(sort_sections=True)

        storage = STStorage(
            self.storage_service,
            area_id,
            st_storage_name,
            properties,
        )

        # Create empty matrices
        series = pd.DataFrame()
        cluster_id = storage.id
        for ts in [
            TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION,
            TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL,
            TimeSeriesFileType.ST_STORAGE_INFLOWS,
            TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE,
            TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE,
        ]:
            write_timeseries(self.config.study_path, series, ts, area_id, cluster_id=cluster_id)

        return storage

    @override
    def set_wind(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.WIND, area_id)
        PreproFolder.WIND.save(self.config.study_path, area_id)

    @override
    def set_reserves(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.RESERVES, area_id)

    @override
    def set_solar(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.SOLAR, area_id)
        PreproFolder.SOLAR.save(self.config.study_path, area_id)

    @override
    def set_misc_gen(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.MISC_GEN, area_id)

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

        study_path = self.config.study_path
        areas_directory = study_path / "input" / "areas"
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

            with (study_path / InitializationFilesTypes.AREAS_SETS_INI.value).open("w") as sets_ini:
                sets_ini_content.write(sets_ini)

            properties = properties or AreaProperties()
            local_properties = AreaPropertiesLocal.from_user_model(properties)

            adequacy_patch_ini = IniFile(study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area_name)
            adequacy_patch_ini.add_section(local_properties.to_adequacy_ini())
            adequacy_patch_ini.write_ini_file()

            optimization_ini = ConfigParser()
            optimization_ini.read_dict(local_properties.to_optimization_ini())

            with open(new_area_directory / "optimization.ini", "w") as optimization_ini_file:
                optimization_ini.write(optimization_ini_file)

            areas_ini = IniFile(study_path, InitializationFilesTypes.THERMAL_AREAS_INI)
            if not areas_ini.ini_dict:
                areas_ini.add_section({"unserverdenergycost": {}})
                areas_ini.add_section({"spilledenergycost": {}})
                areas_ini.write_ini_file()

            areas_ini.parsed_ini["unserverdenergycost"][area_name] = str(local_properties.energy_cost_unsupplied)
            areas_ini.parsed_ini["spilledenergycost"][area_name] = str(local_properties.energy_cost_spilled)
            areas_ini.write_ini_file()

            ui = ui or AreaUi()
            local_ui = AreaUiLocal.from_user_model(ui)
            ui_ini = ConfigParser()
            ui_ini.read_dict(local_ui.model_dump(mode="json", by_alias=True))
            with open(new_area_directory / "ui.ini", "w") as ui_ini_file:
                ui_ini.write(ui_ini_file)

            empty_df = pd.DataFrame()
            self.set_reserves(area_name, empty_df)
            self.set_misc_gen(area_name, empty_df)
            self.set_load(area_name, empty_df)
            self.set_solar(area_name, empty_df)
            self.set_wind(area_name, empty_df)
            IniFile.create_link_ini_for_area(study_path, area_name)
            IniFile.create_list_ini_for_area(study_path, area_name)

            # Hydro
            area_id = transform_name_to_id(area_name)
            default_hydro_properties = HydroProperties()
            update_properties = default_hydro_properties.to_update_properties()
            edit_hydro_properties(study_path, area_id, update_properties, creation=True)
            hydro = Hydro(self.hydro_service, area_id, default_hydro_properties)
            # Create files
            IniFile.create_hydro_initialization_files_for_area(study_path, area_id)
            for ts in [
                TimeSeriesFileType.HYDRO_MAX_POWER,
                TimeSeriesFileType.HYDRO_RESERVOIR,
                TimeSeriesFileType.HYDRO_INFLOW_PATTERN,
                TimeSeriesFileType.HYDRO_CREDITS_MODULATION,
                TimeSeriesFileType.HYDRO_WATER_VALUES,
                TimeSeriesFileType.HYDRO_ROR,
                TimeSeriesFileType.HYDRO_MOD,
                TimeSeriesFileType.HYDRO_MINGEN,
                TimeSeriesFileType.HYDRO_ENERGY,
            ]:
                write_timeseries(study_path, pd.DataFrame(), ts, area_id=area_id)

        except Exception as e:
            raise AreaCreationError(area_name, f"{e}") from e

        logging.info(f"Area {area_name} created successfully!")
        created_area = Area(
            name=area_name,
            area_service=self,
            storage_service=self.storage_service,
            thermal_service=self.thermal_service,
            renewable_service=self.renewable_service,
            hydro_service=self.hydro_service,
            hydro=hydro,
            properties=local_properties.to_user_model(),  # round-trip to do the validation inside Pydantic
            ui=local_ui.to_user_model(),
        )
        return created_area

    @override
    def delete_area(self, area_id: str) -> None:
        raise NotImplementedError

    @override
    def update_area_properties(self, area_id: str, properties: AreaPropertiesUpdate) -> AreaProperties:
        study_path = self.config.study_path
        local_properties = AreaPropertiesLocal.from_user_model(properties)

        # Adequacy patch
        adequacy_patch_ini = IniFile(study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area_id)
        updated_properties_dict: dict[str, Any] = adequacy_patch_ini.ini_dict
        if properties.adequacy_patch_mode:
            updated_properties_dict = local_properties.to_adequacy_ini()
            adequacy_patch_ini.ini_dict = updated_properties_dict
            adequacy_patch_ini.write_ini_file()

        # Thermal properties
        thermal_ini = IniFile(study_path, InitializationFilesTypes.THERMAL_AREAS_INI)
        current_content = thermal_ini.ini_dict
        updated_properties_dict["energy_cost_unsupplied"] = current_content["unserverdenergycost"][area_id]
        updated_properties_dict["energy_cost_spilled"] = current_content["spilledenergycost"][area_id]
        if properties.energy_cost_spilled or properties.energy_cost_unsupplied:
            if properties.energy_cost_spilled:
                current_content["spilledenergycost"][area_id] = properties.energy_cost_spilled
                updated_properties_dict["energy_cost_spilled"] = properties.energy_cost_spilled
            if properties.energy_cost_unsupplied:
                current_content["unserverdenergycost"][area_id] = properties.energy_cost_unsupplied
                updated_properties_dict["energy_cost_unsupplied"] = properties.energy_cost_unsupplied
            thermal_ini.ini_dict = current_content
            thermal_ini.write_ini_file()

        # Optimization properties
        optimization_ini = IniFile(study_path, InitializationFilesTypes.AREA_OPTIMIZATION_INI, area_id=area_id)
        current_content = optimization_ini.ini_dict
        updated_properties_dict.update(current_content)
        if (
            properties.filter_synthesis
            or properties.filter_by_year
            or properties.non_dispatch_power
            or properties.dispatch_hydro_power
            or properties.other_dispatch_power
            or properties.spread_spilled_energy_cost
            or properties.spread_unsupplied_energy_cost
        ):
            new_content = local_properties.to_optimization_ini()
            current_content.update(new_content)
            updated_properties_dict.update(new_content)
            optimization_ini.ini_dict = current_content
            optimization_ini.write_ini_file()

        new_properties = AreaPropertiesLocal.model_validate(updated_properties_dict)
        return new_properties.to_user_model()

    @override
    def update_area_ui(self, area_id: str, ui: AreaUiUpdate) -> AreaUi:
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.AREA_UI_INI, area_id=area_id)
        current_content = ini_file.ini_dict
        # Update ui
        local_ui = AreaUiLocal.from_user_model(ui).model_dump(mode="json", exclude_unset=True, by_alias=True)
        current_content.update(local_ui)
        # Update ini file
        ini_file.ini_dict = current_content
        ini_file.write_ini_file()
        # Prepare object to return
        updated_ui = AreaUiLocal.model_validate(current_content)
        return updated_ui.to_user_model()

    @staticmethod
    def _delete_clusters(ini_file: IniFile, names_to_delete: set[str]) -> None:
        clusters_dict = ini_file.ini_dict
        clusters_dict_after_deletion = copy.deepcopy(clusters_dict)
        for cluster_id, cluster in clusters_dict.items():
            if cluster["name"] in names_to_delete:
                del clusters_dict_after_deletion[cluster_id]
        ini_file.ini_dict = clusters_dict_after_deletion
        ini_file.write_ini_file()

    @override
    def delete_thermal_clusters(self, area_id: str, thermal_clusters: List[ThermalCluster]) -> None:
        thermal_names_to_delete = {th.name for th in thermal_clusters}
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_LIST_INI, area_id=area_id)
        self._delete_clusters(ini_file, thermal_names_to_delete)

    @override
    def delete_renewable_clusters(self, area_id: str, renewable_clusters: List[RenewableCluster]) -> None:
        renewable_names_to_delete = {renewable.name for renewable in renewable_clusters}
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.RENEWABLES_LIST_INI, area_id=area_id)
        self._delete_clusters(ini_file, renewable_names_to_delete)

    @override
    def delete_st_storages(self, area_id: str, storages: List[STStorage]) -> None:
        storage_names_to_delete = {st.name for st in storages}
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id=area_id)
        self._delete_clusters(ini_file, storage_names_to_delete)

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
        if not areas_path.exists():
            return []
        areas = []
        for element in areas_path.iterdir():
            if element.is_dir():
                optimization_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_OPTIMIZATION_INI, area_id=element.name
                ).ini_dict
                area_adequacy_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area_id=element.name
                ).ini_dict
                thermal_area_dict = IniFile(self.config.study_path, InitializationFilesTypes.THERMAL_AREAS_INI).ini_dict
                unserverd_energy_cost = thermal_area_dict.get("unserverdenergycost", {}).get(element.name, 0)
                spilled_energy_cost = thermal_area_dict.get("spilledenergycost", {}).get(element.name, 0)
                local_properties_dict = {
                    **optimization_dict,
                    **area_adequacy_dict,
                    "energy_cost_unsupplied": unserverd_energy_cost,
                    "energy_cost_spilled": spilled_energy_cost,
                }
                local_properties = AreaPropertiesLocal.model_validate(local_properties_dict)
                area_properties = local_properties.to_user_model()
                ui_dict = IniFile(
                    self.config.study_path, InitializationFilesTypes.AREA_UI_INI, area_id=element.name
                ).ini_dict

                local_ui = AreaUiLocal.model_validate(ui_dict)
                ui_properties = local_ui.to_user_model()

                area = Area(
                    name=element.name,
                    area_service=self,
                    storage_service=self.storage_service,
                    thermal_service=self.thermal_service,
                    renewable_service=self.renewable_service,
                    hydro_service=self.hydro_service,
                    properties=area_properties,
                    ui=ui_properties,
                )
                area.hydro._read_properties()
                areas.append(area)

        areas.sort(key=lambda area_obj: area_obj.id)
        return areas

    @override
    def update_multiple_areas(self, dict_areas: Dict[str, AreaPropertiesUpdate]) -> Dict[str, AreaProperties]:
        new_properties_dict = {}
        for area_id, update_properties in dict_areas.items():
            new_properties = self.update_area_properties(area_id, update_properties)
            new_properties_dict[area_id] = new_properties
        return new_properties_dict
