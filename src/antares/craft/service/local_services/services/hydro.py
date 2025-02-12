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

import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.hydro import HydroPropertiesUpdate
from antares.craft.service.base_services import BaseHydroService
from antares.craft.service.local_services.models.hydro import HydroPropertiesLocal, HydroPropertiesLocalUpdate
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.matrix_tool import read_timeseries
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
    list_ini.write_ini_file()
