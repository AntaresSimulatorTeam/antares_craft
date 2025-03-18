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
from pathlib import Path
from typing import Any

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate, InflowStructure, InflowStructureUpdate
from antares.craft.service.base_services import BaseHydroService
from antares.craft.service.local_services.models.hydro import (
    HydroInflowStructureLocal,
    HydroPropertiesLocal,
    HydroPropertiesLocalUpdate,
)
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from typing_extensions import override


class HydroLocalService(BaseHydroService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self.study_name = study_name

    @override
    def update_properties(self, area_id: str, properties: HydroPropertiesUpdate) -> None:
        edit_hydro_properties(self.config.study_path, area_id, properties, creation=False)

    @override
    def update_inflow_structure(self, area_id: str, inflow_structure: InflowStructureUpdate) -> None:
        ini_file = IniFile(self.config.study_path, InitializationFilesTypes.HYDRO_PREPRO_INI, area_id=area_id)
        ini_file.ini_dict = HydroInflowStructureLocal.from_user_model(inflow_structure).model_dump(by_alias=True)
        ini_file.write_ini_file()

    @override
    def read_properties(self) -> dict[str, HydroProperties]:
        hydro_properties: dict[str, HydroProperties] = {}

        list_ini = IniFile(self.config.study_path, InitializationFilesTypes.HYDRO_INI)
        current_content = list_ini.ini_dict

        body_by_area: dict[str, dict[str, Any]] = {}
        for key, value in current_content.items():
            for area_id, data in value.items():
                body_by_area.setdefault(area_id, {})[key] = data
        for area_id, local_properties in body_by_area.items():
            user_properties = HydroPropertiesLocal.model_validate(local_properties).to_user_model()
            hydro_properties[area_id] = user_properties

        return hydro_properties

    @override
    def read_inflow_structure(self) -> dict[str, InflowStructure]:
        all_inflow_structure: dict[str, InflowStructure] = {}

        prepro_path = self.config.study_path / "input" / "hydro" / "prepro"
        if not prepro_path.exists():
            return {}
        for element in prepro_path.iterdir():
            if element.is_dir():
                ini_file = IniFile(
                    self.config.study_path, InitializationFilesTypes.HYDRO_PREPRO_INI, area_id=element.name
                )
                inflow_structure = HydroInflowStructureLocal.model_validate(ini_file.ini_dict).to_user_model()
                all_inflow_structure[element.name] = inflow_structure

        return all_inflow_structure

    @override
    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_MAX_POWER, self.config.study_path, area_id=area_id)

    @override
    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_RESERVOIR, self.config.study_path, area_id=area_id)

    @override
    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_INFLOW_PATTERN, self.config.study_path, area_id=area_id)

    @override
    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_CREDITS_MODULATION, self.config.study_path, area_id=area_id)

    @override
    def get_water_values(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_WATER_VALUES, self.config.study_path, area_id=area_id)

    @override
    def get_ror_series(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_ROR, self.config.study_path, area_id=area_id)

    @override
    def get_mod_series(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_MOD, self.config.study_path, area_id=area_id)

    @override
    def get_mingen(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_MINGEN, self.config.study_path, area_id=area_id)

    @override
    def get_energy(self, area_id: str) -> pd.DataFrame:
        return read_timeseries(TimeSeriesFileType.HYDRO_ENERGY, self.config.study_path, area_id=area_id)

    @override
    def set_maxpower(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_MAX_POWER, area_id)

    @override
    def set_reservoir(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_RESERVOIR, area_id)

    @override
    def set_inflow_pattern(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_INFLOW_PATTERN, area_id)

    @override
    def set_credits_modulation(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_CREDITS_MODULATION, area_id)

    @override
    def set_water_values(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_WATER_VALUES, area_id)

    @override
    def set_ror_series(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_ROR, area_id)

    @override
    def set_mod_series(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_MOD, area_id)

    @override
    def set_mingen(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_MINGEN, area_id)

    @override
    def set_energy(self, area_id: str, series: pd.DataFrame) -> None:
        write_timeseries(self.config.study_path, series, TimeSeriesFileType.HYDRO_ENERGY, area_id)


def edit_hydro_properties(study_path: Path, area_id: str, properties: HydroPropertiesUpdate, creation: bool) -> None:
    list_ini = IniFile(study_path, InitializationFilesTypes.HYDRO_INI)
    current_content = list_ini.ini_dict

    if creation:
        local_dict = HydroPropertiesLocal.from_user_model(properties).model_dump(mode="json", by_alias=True)
    else:
        local_update_properties = HydroPropertiesLocalUpdate.from_user_model(properties)
        local_dict = local_update_properties.model_dump(mode="json", by_alias=True, exclude_none=True)

    for key, value in local_dict.items():
        current_content.setdefault(key, {})[area_id] = value
    list_ini.ini_dict = current_content
    list_ini.write_ini_file(sort_section_content=True)
