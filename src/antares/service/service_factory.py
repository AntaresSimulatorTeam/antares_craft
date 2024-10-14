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
import os
from pathlib import Path
from antares.api_conf.api_conf import APIconf
from antares.config.base_configuration import BaseConfiguration
from antares.config.local_configuration import LocalConfiguration
from antares.service.api_services.area_api import AreaApiService
from antares.service.api_services.binding_constraint_api import (
    BindingConstraintApiService,
)
from antares.service.api_services.link_api import LinkApiService
from antares.service.api_services.renewable_api import RenewableApiService
from antares.service.api_services.st_storage_api import ShortTermStorageApiService
from antares.service.api_services.study_api import StudyApiService
from antares.service.api_services.thermal_api import ThermalApiService
from antares.service.base_services import (
    BaseAreaService,
    BaseLinkService,
    BaseThermalService,
    BaseBindingConstraintService,
    BaseStudyService,
    BaseRenewableService,
    BaseShortTermStorageService,
)
from antares.service.local_services.area_local import AreaLocalService
from antares.service.local_services.binding_constraint_local import (
    BindingConstraintLocalService,
)
from antares.service.local_services.link_local import LinkLocalService
from antares.service.local_services.renewable_local import RenewableLocalService
from antares.service.local_services.st_storage_local import ShortTermStorageLocalService
from antares.service.local_services.study_local import StudyLocalService
from antares.service.local_services.thermal_local import ThermalLocalService
from antares.tools.ini_tool import IniFileTypes, IniFile
from antares.tools.time_series_tool import TimeSeriesFileType, TimeSeriesFile

ERROR_MESSAGE = "Unsupported configuration type: "


class ServiceFactory:
    def __init__(self, config: BaseConfiguration, study_id: str = "", study_name: str = ""):
        self.config = config
        self.study_id = study_id
        self.study_name = study_name

    def create_area_service(self) -> BaseAreaService:
        if isinstance(self.config, APIconf):
            area_service: BaseAreaService = AreaApiService(self.config, self.study_id)
            storage_service: BaseShortTermStorageService = ShortTermStorageApiService(self.config, self.study_id)
            thermal_service: BaseThermalService = ThermalApiService(self.config, self.study_id)
            renewable_service: BaseRenewableService = RenewableApiService(self.config, self.study_id)
            area_service.set_storage_service(storage_service)
            area_service.set_thermal_service(thermal_service)
            area_service.set_renewable_service(renewable_service)
        elif isinstance(self.config, LocalConfiguration):
            area_service = AreaLocalService(self.config, self.study_name)
            storage_service = ShortTermStorageLocalService(self.config, self.study_name)
            thermal_service = ThermalLocalService(self.config, self.study_name)
            renewable_service = RenewableLocalService(self.config, self.study_name)
            area_service.set_storage_service(storage_service)
            area_service.set_thermal_service(thermal_service)
            area_service.set_renewable_service(renewable_service)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return area_service

    def create_link_service(self) -> BaseLinkService:
        if isinstance(self.config, APIconf):
            link_service: BaseLinkService = LinkApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            link_service = LinkLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return link_service

    def create_thermal_service(self) -> BaseThermalService:
        if isinstance(self.config, APIconf):
            thermal_service: BaseThermalService = ThermalApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            thermal_service = ThermalLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return thermal_service

    def create_binding_constraints_service(self) -> BaseBindingConstraintService:
        if isinstance(self.config, APIconf):
            binding_constraint_service: BaseBindingConstraintService = BindingConstraintApiService(
                self.config, self.study_id
            )
        elif isinstance(self.config, LocalConfiguration):
            binding_constraint_service = BindingConstraintLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return binding_constraint_service

    def create_study_service(self) -> BaseStudyService:
        if isinstance(self.config, APIconf):
            study_service: BaseStudyService = StudyApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            study_service = StudyLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return study_service

    def create_renewable_service(self) -> BaseRenewableService:
        if isinstance(self.config, APIconf):
            renewable_service: BaseRenewableService = RenewableApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            renewable_service = RenewableLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return renewable_service

    def create_st_storage_service(self) -> BaseShortTermStorageService:
        if isinstance(self.config, APIconf):
            short_term_storage_service: BaseShortTermStorageService = ShortTermStorageApiService(
                self.config, self.study_id
            )
        elif isinstance(self.config, LocalConfiguration):
            short_term_storage_service = ShortTermStorageLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return short_term_storage_service


class ServiceReader:
    def __init__(
        self, config: BaseConfiguration, study_name: Path = "", study_id: str = ""
    ):
        self.config = config
        self.study_id = study_id
        self.study_name = study_name
        self._areas = {}
        self._binding_constraints = []
        self._links = []
        self._thermals = {}
        self._renewables = {}
        self._load = {}
        self._solar = {}
        self._wind = {}
        self._misc = {}
        self._storage = {}
        self._hydro = {}
        self._study = {}

    @staticmethod
    def _directory_exists(local_path: Path) -> None:
        if local_path is None or not os.path.exists(local_path):
            return False
        return True

    @staticmethod
    def _lister_dossiers(dossier):
        try:
            dossiers = [
                d
                for d in os.listdir(dossier)
                if os.path.isdir(os.path.join(dossier, d))
            ]
            return dossiers
        except FileNotFoundError:
            return []

    # we can have read area service here, for just one area
    def read_study_service(self) -> BaseStudyService:
        if isinstance(self.config, LocalConfiguration):
            study_service: BaseStudyService = StudyLocalService(
                self.config, self.study_name
            )
            areas = study_service.read_areas()

            study_path = self.config.local_path / self.study_name

            # Get areas/sets.ini file
            sets_ini = IniFile(study_path, IniFileTypes.AREAS_SETS_INI).parsed_ini

            self._areas = {
                section: {key: f"{value}" for key, value in sets_ini.items(section)}
                for section in sets_ini.sections()
            }
            if not self._directory_exists(study_path):
                return {}

            # Areas
            for area_name in areas:
                # Get everything inside input/areas/{area_name}
                area_service: BaseStudyService = AreaLocalService(
                    self.config, self.study_name
                )
                area = area_service.read_area(area_name)
                self._areas[area_name] = area

            # Load
            # Get everything inside input/load/prepro/
            load_correlation_ini = IniFile(
                study_path, IniFileTypes.LOAD_CORRELATION_INI
            ).parsed_ini
            self._load["correlation"] = {
                section: {
                    key: f"{value}"
                    for key, value in load_correlation_ini.items(section)
                }
                for section in load_correlation_ini.sections()
            }
            for area_name in areas:
                self._load[area_name] = {}
                # Get everything inside input/load/prepro/{area_name}
                load_settings_ini = IniFile(
                    study_path, IniFileTypes.LOAD_SETTINGS_INI, area_name
                ).parsed_ini

                self._load[area_name]["settings"] = {
                    section: {
                        key: f"{value}"
                        for key, value in load_settings_ini.items(section)
                    }
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
                load_series = TimeSeriesFile(
                    TimeSeriesFileType.LOAD_DATA_SERIES,
                    study_path,
                    area_name
                ).time_series
                self._load[area_name]["series"] = load_series

            # misc-gen
            for area_name in areas:
                self._misc[area_name] = {}
                # Get everything inside input/misc-gen/{area_name}
                miscgen_series = TimeSeriesFile(
                    TimeSeriesFileType.MISC_GEN,
                    study_path,
                    area_name
                ).time_series
                self._misc[area_name]["series"] = miscgen_series

            # Renewables
            for area_name in areas:
                self._renewables[area_name] = {}

                # Get everything inside input/renewables/clusters/{area_name}
                renewables_list_ini = IniFile(
                    study_path, IniFileTypes.RENEWABLES_LIST_INI, area_name
                ).parsed_ini
                self._renewables[area_name]["list"] = {
                    section: {
                        key: f"{value}"
                        for key, value in renewables_list_ini.items(section)
                    }
                    for section in renewables_list_ini.sections()
                }

                # Get everything inside input/renewables/series/{area_name}
                prefix_path = (
                        study_path
                        / TimeSeriesFileType.RENEWABLE_SERIES_PREFIX.value.format(
                    area_id=area_name
                )
                )
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
            solar_correlation_ini = IniFile(
                study_path, IniFileTypes.SOLAR_CORRELATION_INI
            ).parsed_ini
            self._solar["correlation"] = {
                section: {
                    key: f"{value}"
                    for key, value in solar_correlation_ini.items(section)
                }
                for section in solar_correlation_ini.sections()
            }
            for area_name in areas:
                self._solar[area_name] = {}

                # Get everything inside input/solar/prepro/{area_name}
                solar_settings_ini = IniFile(
                    study_path, IniFileTypes.SOLAR_SETTINGS_INI, area_name
                ).parsed_ini

                self._solar[area_name]["settings"] = {
                    section: {
                        key: f"{value}"
                        for key, value in solar_settings_ini.items(section)
                    }
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
                solar_series = TimeSeriesFile(
                    TimeSeriesFileType.SOLAR,
                    study_path,
                    area_name
                ).time_series
                self._solar[area_name]["series"] = solar_series

            # St-storage
            for area_name in areas:
                self._storage[area_name] = {}
                # Get everything inside input/st-storage/clusters/
                storage_list_ini = IniFile(
                    study_path, IniFileTypes.ST_STORAGE_LIST_INI, area_name
                ).parsed_ini
                self._storage[area_name]["list"] = {
                    section: {
                        key: f"{value}"
                        for key, value in storage_list_ini.items(section)
                    }
                    for section in storage_list_ini.sections()
                }

            # Thermals
            thermal_list_ini = IniFile(
                study_path, IniFileTypes.THERMAL_AREAS_INI
            ).parsed_ini
            self._thermals["areas"] = {
                section: {
                    key: f"{value}"
                    for key, value in thermal_list_ini.items(section)
                }
                for section in thermal_list_ini.sections()
            }
            for area_name in areas:
                self._thermals[area_name] = {}
                # Get everything inside input/thermal/clusters/{area_name}
                thermal_list_ini = IniFile(
                    study_path, IniFileTypes.THERMAL_LIST_INI, area_name
                ).parsed_ini
                self._thermals[area_name]["list"] = {
                    section: {
                        key: f"{value}"
                        for key, value in thermal_list_ini.items(section)
                    }
                    for section in thermal_list_ini.sections()
                }

                # Get everything inside input/thermal/prepro/{area_name}
                prefix_path = (
                    study_path
                    / TimeSeriesFileType.THERMAL_PREFIX.value.format(
                        area_id=area_name
                    )
                )
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
                prefix_path = (
                    study_path
                    / TimeSeriesFileType.THERMAL_SERIES_PREFIX.value.format(
                        area_id=area_name
                    )
                )
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
            wind_correlation_ini = IniFile(
                study_path, IniFileTypes.WIND_CORRELATION_INI
            ).parsed_ini
            self._wind["correlation"] = {
                section: {
                    key: f"{value}"
                    for key, value in wind_correlation_ini.items(section)
                }
                for section in wind_correlation_ini.sections()
            }
            for area_name in areas:
                self._wind[area_name] = {}

                # Get everything inside input/wind/prepro/{area_name}
                wind_settings_ini = IniFile(
                    study_path, IniFileTypes.WIND_SETTINGS_INI, area_name
                ).parsed_ini

                self._wind[area_name]["settings"] = {
                    section: {
                        key: f"{value}"
                        for key, value in wind_settings_ini.items(section)
                    }
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
                wind_series = TimeSeriesFile(
                    TimeSeriesFileType.WIND,
                    study_path,
                    area_name
                ).time_series
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
                section: {key: f"{value}" for key, value in hydro_ini.items(section)}
                for section in hydro_ini.sections()
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

        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return self._study
