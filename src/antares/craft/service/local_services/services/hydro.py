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

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.hydro import HydroProperties, HydroPropertiesUpdate, InflowStructure, InflowStructureUpdate
from antares.craft.service.base_services import BaseHydroService
from antares.craft.service.local_services.models.hydro import (
    HydroInflowStructureLocal,
    parse_hydro_properties_local,
    serialize_hydro_properties_local,
)
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from antares.study.version import StudyVersion


class HydroLocalService(BaseHydroService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion):
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    @staticmethod
    def _transform_areas_name_to_id(content: dict[str, Any]) -> dict[str, Any]:
        for key, values in content.items():
            for area_name in list(values.keys()):
                content[key][transform_name_to_id(area_name)] = content[key].pop(area_name)
        return content

    def _read_ini(self) -> dict[str, Any]:
        content = IniReader().read(self.config.study_path / "input" / "hydro" / "hydro.ini")
        return self._transform_areas_name_to_id(content)

    def _save_ini(self, content: dict[str, Any]) -> None:
        transformed_content = self._transform_areas_name_to_id(content)
        IniWriter().write(transformed_content, self.config.study_path / "input" / "hydro" / "hydro.ini")

    def _get_inflow_path(self, area_id: str) -> Path:
        return self.config.study_path / "input" / "hydro" / "prepro" / area_id / "prepro.ini"

    def _read_inflow_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_inflow_path(area_id))

    def save_inflow_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self._get_inflow_path(area_id))

    def save_allocation_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self.config.study_path / "input" / "hydro" / "allocation" / f"{area_id}.ini")

    @override
    def update_properties(self, area_id: str, properties: HydroPropertiesUpdate) -> None:
        self.edit_hydro_properties(area_id, properties, creation=False)

    @override
    def update_inflow_structure(self, area_id: str, inflow_structure: InflowStructureUpdate) -> None:
        new_content = HydroInflowStructureLocal.from_user_model(inflow_structure).model_dump(by_alias=True)
        self.save_inflow_ini(new_content, area_id)

    @override
    def read_inflow_structure_for_one_area(self, area_id: str) -> InflowStructure:
        prepro_dict = self._read_inflow_ini(area_id)
        return HydroInflowStructureLocal.model_validate(prepro_dict).to_user_model()

    @override
    def read_properties_and_inflow_structure(self) -> dict[str, tuple[HydroProperties, InflowStructure]]:
        response: dict[str, tuple[HydroProperties, InflowStructure]] = {}

        all_properties = self.read_properties()
        for area_id, hydro_properties in all_properties.items():
            inflow_structure = self.read_inflow_structure_for_one_area(area_id)
            response[area_id] = (hydro_properties, inflow_structure)

        return response

    def read_properties(self) -> dict[str, HydroProperties]:
        hydro_properties: dict[str, HydroProperties] = {}

        current_content = self._read_ini()

        body_by_area: dict[str, dict[str, Any]] = {}
        for key, value in current_content.items():
            for area_id, data in value.items():
                body_by_area.setdefault(area_id, {})[key] = data
        for area_id, local_properties in body_by_area.items():
            user_properties = parse_hydro_properties_local(self.study_version, local_properties)
            hydro_properties[area_id] = user_properties

        return hydro_properties

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

    def edit_hydro_properties(self, area_id: str, properties: HydroPropertiesUpdate, creation: bool) -> None:
        current_content = self._read_ini()

        local_dict = serialize_hydro_properties_local(self.study_version, properties, exclude_unset=not creation)

        for key, value in local_dict.items():
            current_content.setdefault(key, {})[area_id] = value
        self._save_ini(current_content)
