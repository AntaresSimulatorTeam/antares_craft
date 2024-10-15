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

import json
import os

from pathlib import Path
from typing import Any, Optional

from antares.config.local_configuration import LocalConfiguration
from antares.model.binding_constraint import BindingConstraint
from antares.model.settings import StudySettings
from antares.service.base_services import (
    BaseStudyService,
)
from antares.service.local_services.area_local import AreaLocalService
from antares.tools.ini_tool import IniFile, IniFileTypes
from antares.tools.time_series_tool import TimeSeriesFile, TimeSeriesFileType


class StudyLocalService(BaseStudyService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._study_name = study_name
        self._areas: dict[str, list] = {}
        # self._binding_constraints = []
        # self._links = []
        self._thermals: dict[str, dict] = {}
        self._renewables: dict[str, dict] = {}
        self._load: dict[str, dict] = {}
        self._solar: dict[str, dict] = {}
        self._wind: dict[str, dict] = {}
        self._misc: dict[str, dict] = {}
        self._storage: dict[str, dict] = {}
        self._hydro: dict[str, dict] = {}
        self._study: dict[str, dict] = {}

    @property
    def study_id(self) -> str:
        return self._study_name

    @property
    def config(self) -> LocalConfiguration:
        return self._config

    @staticmethod
    def _directory_exists(local_path: Path) -> bool:
        if local_path is None or not os.path.exists(local_path):
            return False
        return True

    @staticmethod
    def _lister_dossiers(dossier: Path) -> list[str]:
        try:
            dossiers = [d for d in os.listdir(dossier) if os.path.isdir(os.path.join(dossier, d))]
            return dossiers
        except FileNotFoundError:
            return []

    def update_study_settings(self, settings: StudySettings) -> Optional[StudySettings]:
        raise NotImplementedError

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        raise NotImplementedError

    def delete(self, children: bool) -> None:
        raise NotImplementedError

    def read_areas(self) -> dict:
        local_path = self._config.local_path

        patch_path = local_path / Path(self._study_name) / Path("patch.json")
        if not os.path.exists(patch_path):
            return json.loads(f"Le fichier {patch_path} n'existe pas dans le dossier {local_path / self._study_name}")
        try:
            with open(patch_path, "r") as file:
                content = file.read()
                try:
                    data = json.loads(content)
                except json.JSONDecodeError:
                    return json.loads(f"Le fichier {patch_path} ne contient pas du JSON valide")
                if "areas" in data:
                    areas = data["areas"]
                    if isinstance(areas, dict):
                        return {key: None for key in areas.keys()}
                return json.loads("The key 'areas' n'existe pas dans le fichier JSON")

        except IOError:
            return json.loads(f"Impossible de lire le fichier {patch_path}")

    def read_study(self, areas: dict) -> dict:
        study_path = self.config.local_path / Path(self._study_name)
        # Get areas/sets.ini file
        sets_ini = IniFile(study_path, IniFileTypes.AREAS_SETS_INI).parsed_ini

        self._areas = {
            section: [(key, f"{value}") for key, value in sets_ini.items(section)] for section in sets_ini.sections()
        }
        if not self._directory_exists(study_path):
            return {}

        # Areas
        for area_name in areas:
            # Get everything inside input/areas/{area_name}
            area_service = AreaLocalService(self.config, self._study_name)
            area = area_service.read_area(area_name)
            self._areas[area_name] = area

        # Load
        # Get everything inside input/load/prepro/
        load_correlation_ini = IniFile(study_path, IniFileTypes.LOAD_CORRELATION_INI).parsed_ini
        self._load["correlation"] = {
            section: {key: f"{value}" for key, value in load_correlation_ini.items(section)}
            for section in load_correlation_ini.sections()
        }
        for area_name in areas:
            self._load[area_name] = {}
            # Get everything inside input/load/prepro/{area_name}
            load_settings_ini = IniFile(study_path, IniFileTypes.LOAD_SETTINGS_INI, area_name).parsed_ini

            self._load[area_name]["settings"] = {
                section: {key: f"{value}" for key, value in load_settings_ini.items(section)}
                for section in load_settings_ini.sections()
            }

            load_module = TimeSeriesFile(
                TimeSeriesFileType.LOAD_PREPRO_TRANSLATION,
                study_path,
                area_name,
            ).time_series
            self._load[area_name]["translation"] = load_module
            load_module = TimeSeriesFile(
                TimeSeriesFileType.LOAD_PREPRO_CONVERSION,
                study_path,
                area_name,
            ).time_series
            self._load[area_name]["conversion"] = load_module
            load_module = TimeSeriesFile(
                TimeSeriesFileType.LOAD_PREPRO_DATA,
                study_path,
                area_name,
            ).time_series
            self._load[area_name]["data"] = load_module
            load_module = TimeSeriesFile(
                TimeSeriesFileType.LOAD_PREPRO_K,
                study_path,
                area_name,
            ).time_series
            self._load[area_name]["k"] = load_module

            # Get everything inside input/load/series/{area_name}
            load_series = TimeSeriesFile(TimeSeriesFileType.LOAD_DATA_SERIES, study_path, area_name).time_series
            self._load[area_name]["series"] = load_series

        # misc-gen
        for area_name in areas:
            self._misc[area_name] = {}
            # Get everything inside input/misc-gen/{area_name}
            miscgen_series = TimeSeriesFile(TimeSeriesFileType.MISC_GEN, study_path, area_name).time_series
            self._misc[area_name]["series"] = miscgen_series

        # Renewables
        for area_name in areas:
            self._renewables[area_name] = {}

            # Get everything inside input/renewables/clusters/{area_name}
            renewables_list_ini = IniFile(study_path, IniFileTypes.RENEWABLES_LIST_INI, area_name).parsed_ini
            self._renewables[area_name]["list"] = {
                section: {key: f"{value}" for key, value in renewables_list_ini.items(section)}
                for section in renewables_list_ini.sections()
            }

            # Get everything inside input/renewables/series/{area_name}
            prefix_path = study_path / TimeSeriesFileType.RENEWABLE_SERIES_PREFIX.value.format(area_id=area_name)
            groups = self._lister_dossiers(prefix_path)
            for group_name in groups:
                renewable_series = TimeSeriesFile(
                    TimeSeriesFileType.RENEWABLE_DATA_SERIES,
                    study_path,
                    area_name,
                    group_name,
                ).time_series
                self._renewables[area_name][f"{group_name}-series"] = renewable_series

        # Solar
        # Get everything inside input/solar/prepro/
        solar_correlation_ini = IniFile(study_path, IniFileTypes.SOLAR_CORRELATION_INI).parsed_ini
        self._solar["correlation"] = {
            section: {key: f"{value}" for key, value in solar_correlation_ini.items(section)}
            for section in solar_correlation_ini.sections()
        }
        for area_name in areas:
            self._solar[area_name] = {}

            # Get everything inside input/solar/prepro/{area_name}
            solar_settings_ini = IniFile(study_path, IniFileTypes.SOLAR_SETTINGS_INI, area_name).parsed_ini

            self._solar[area_name]["settings"] = {
                section: {key: f"{value}" for key, value in solar_settings_ini.items(section)}
                for section in solar_settings_ini.sections()
            }

            solar_module = TimeSeriesFile(
                TimeSeriesFileType.SOLAR_TRANSLATION,
                study_path,
                area_name,
            ).time_series
            self._solar[area_name]["translation"] = solar_module
            solar_module = TimeSeriesFile(
                TimeSeriesFileType.SOLAR_CONVERSION,
                study_path,
                area_name,
            ).time_series
            self._solar[area_name]["conversion"] = solar_module
            solar_module = TimeSeriesFile(
                TimeSeriesFileType.SOLAR_DATA,
                study_path,
                area_name,
            ).time_series
            self._solar[area_name]["data"] = solar_module
            solar_module = TimeSeriesFile(
                TimeSeriesFileType.SOLAR_K,
                study_path,
                area_name,
            ).time_series
            self._solar[area_name]["k"] = solar_module

            # Get everything inside input/solar/series/{area_name}
            solar_series = TimeSeriesFile(TimeSeriesFileType.SOLAR, study_path, area_name).time_series
            self._solar[area_name]["series"] = solar_series

        # St-storage
        for area_name in areas:
            self._storage[area_name] = {}
            # Get everything inside input/st-storage/clusters/
            storage_list_ini = IniFile(study_path, IniFileTypes.ST_STORAGE_LIST_INI, area_name).parsed_ini
            self._storage[area_name]["list"] = {
                section: {key: f"{value}" for key, value in storage_list_ini.items(section)}
                for section in storage_list_ini.sections()
            }

        # Thermals
        thermal_list_ini = IniFile(study_path, IniFileTypes.THERMAL_AREAS_INI).parsed_ini
        self._thermals["areas"] = {
            section: {key: f"{value}" for key, value in thermal_list_ini.items(section)}
            for section in thermal_list_ini.sections()
        }
        for area_name in areas:
            self._thermals[area_name] = {}
            # Get everything inside input/thermal/clusters/{area_name}
            thermal_list_ini = IniFile(study_path, IniFileTypes.THERMAL_LIST_INI, area_name).parsed_ini
            self._thermals[area_name]["list"] = {
                section: {key: f"{value}" for key, value in thermal_list_ini.items(section)}
                for section in thermal_list_ini.sections()
            }

            # Get everything inside input/thermal/prepro/{area_name}
            prefix_path = study_path / TimeSeriesFileType.THERMAL_PREFIX.value.format(area_id=area_name)
            groups = self._lister_dossiers(prefix_path)
            for group_name in groups:
                thermal_prepro = TimeSeriesFile(
                    TimeSeriesFileType.THERMAL_DATA,
                    study_path,
                    area_name,
                    group_name,
                ).time_series
                self._thermals[area_name][f"{group_name}-data"] = thermal_prepro
                thermal_module = TimeSeriesFile(
                    TimeSeriesFileType.THERMAL_MODULATION,
                    study_path,
                    area_name,
                    group_name,
                ).time_series
                self._thermals[area_name][f"{group_name}-modulation"] = thermal_module

            # Get everything inside input/thermal/series/{area_name}
            prefix_path = study_path / TimeSeriesFileType.THERMAL_SERIES_PREFIX.value.format(area_id=area_name)
            groups = self._lister_dossiers(prefix_path)
            for group_name in groups:
                thermal_series = TimeSeriesFile(
                    TimeSeriesFileType.THERMAL_DATA_SERIES,
                    study_path,
                    area_name,
                    group_name,
                ).time_series
                self._thermals[area_name][f"{group_name}-series"] = thermal_series

        # Wind
        # Get everything inside input/wind/prepro/
        wind_correlation_ini = IniFile(study_path, IniFileTypes.WIND_CORRELATION_INI).parsed_ini
        self._wind["correlation"] = {
            section: {key: f"{value}" for key, value in wind_correlation_ini.items(section)}
            for section in wind_correlation_ini.sections()
        }
        for area_name in areas:
            self._wind[area_name] = {}

            # Get everything inside input/wind/prepro/{area_name}
            wind_settings_ini = IniFile(study_path, IniFileTypes.WIND_SETTINGS_INI, area_name).parsed_ini

            self._wind[area_name]["settings"] = {
                section: {key: f"{value}" for key, value in wind_settings_ini.items(section)}
                for section in wind_settings_ini.sections()
            }

            wind_module = TimeSeriesFile(
                TimeSeriesFileType.WIND_TRANSLATION,
                study_path,
                area_name,
            ).time_series
            self._wind[area_name]["translation"] = wind_module

            wind_module = TimeSeriesFile(
                TimeSeriesFileType.WIND_CONVERSION,
                study_path,
                area_name,
            ).time_series
            self._wind[area_name]["conversion"] = wind_module

            wind_module = TimeSeriesFile(
                TimeSeriesFileType.WIND_DATA,
                study_path,
                area_name,
            ).time_series
            self._wind[area_name]["data"] = wind_module

            wind_module = TimeSeriesFile(
                TimeSeriesFileType.WIND_K,
                study_path,
                area_name,
            ).time_series
            self._wind[area_name]["k"] = wind_module

            # Get everything inside input/wind/series/{area_name}
            wind_series = TimeSeriesFile(TimeSeriesFileType.WIND, study_path, area_name).time_series
            self._wind[area_name]["series"] = wind_series

        ## Hydro
        # Get everything inside input/hydro/prepro/
        correlation_ini = IniFile(study_path, IniFileTypes.HYDRO_CORRELATION_INI).parsed_ini
        self._hydro["correlation"] = {
            section: {key: f"{value}" for key, value in correlation_ini.items(section)}
            for section in correlation_ini.sections()
        }
        # Get areas/sets.ini file
        hydro_ini = IniFile(study_path, IniFileTypes.HYDRO_INI).parsed_ini
        self._hydro["hydro"] = {
            section: {key: f"{value}" for key, value in hydro_ini.items(section)} for section in hydro_ini.sections()
        }
        for area_name in areas:
            self._hydro[area_name] = {}
            # Get everything inside input/hydro/allocation
            hydro_ini = IniFile(study_path, IniFileTypes.HYDRO_ALLOCATION_INI, area_name).parsed_ini
            self._hydro[area_name]["allocation"] = {
                section: {key: f"{value}" for key, value in hydro_ini.items(section)}
                for section in hydro_ini.sections()
            }
            # Get everything inside input/hydro/common/capacity/
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_COMMON_CM,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["creditmodulations"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_COMMON_IFP,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["inflowpattern"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_COMMON_MP,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["maxpower"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_COMMON_R,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["reservoir"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_COMMON_WV,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["watervalues"] = hydro_module

            # Get everything inside input/hydro/prepro/{area_name}
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_ENERGY,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["energy"] = hydro_module

            hydro_ini = IniFile(study_path, IniFileTypes.HYDRO_PREPRO_INI, area_name).parsed_ini
            self._hydro[area_name]["prepro"] = {
                section: {key: f"{value}" for key, value in hydro_ini.items(section)}
                for section in hydro_ini.sections()
            }

            # Get everything inside input/hydro/series/{area_name}
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_MINGEN_SERIES,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["mingen"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_MOD_SERIES,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["mod"] = hydro_module
            hydro_module = TimeSeriesFile(
                TimeSeriesFileType.HYDRO_ROR_SERIES,
                study_path,
                area_name,
            ).time_series
            self._hydro[area_name]["ror"] = hydro_module

        self._study["areas"] = self._areas
        self._study["hydro"] = self._hydro
        self._study["load"] = self._load
        self._study["misc"] = self._misc
        self._study["renewables"] = self._renewables
        self._study["solar"] = self._solar
        self._study["storage"] = self._storage
        self._study["thermals"] = self._thermals
        self._study["wind"] = self._wind

        return self._study
