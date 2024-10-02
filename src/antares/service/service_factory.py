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

    @staticmethod
    def _directory_not_exists(local_path: Path) -> None:
        if local_path is None or not os.path.exists(local_path):
            return False
        return True

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
            for area_name in areas:
                # Get everything inside input/areas/{area_name}
                area_service: BaseStudyService = AreaLocalService(
                    self.config, self.study_name
                )
                area = area_service.read_area(area_name)
                self._areas[area_name] = area

                # Get everything inside input/thermal/clusters/{area_name}
                if self._directory_not_exists(study_path):
                    thermal_list_ini = IniFile(
                        study_path, IniFileTypes.THERMAL_LIST_INI, area_name
                    ).parsed_ini
                    self._thermals = {
                        section: {
                            key: f"{value}"
                            for key, value in thermal_list_ini.items(section)
                        }
                        for section in thermal_list_ini.sections()
                    }

                # Get everything inside input/thermal/prepro/{area_name}
                def lister_dossiers(dossier):
                    try:
                        dossiers = [
                            d
                            for d in os.listdir(dossier)
                            if os.path.isdir(os.path.join(dossier, d))
                        ]
                        return dossiers
                    except FileNotFoundError:
                        return []

                prefix_path = (
                    study_path
                    / TimeSeriesFileType.THERMAL_PREPRO_PREFIX.value.format(
                        area_id=area_name
                    )
                )
                groups = lister_dossiers(prefix_path)
                if self._directory_not_exists(study_path):
                    for group_name in groups:
                        thermal_prepro = TimeSeriesFile(
                            TimeSeriesFileType.THERMAL_DATA,
                            study_path,
                            area_name,
                            group_name,
                        ).time_series
                        self._thermals[f"{group_name}-data"] = thermal_prepro
                        thermal_module = TimeSeriesFile(
                            TimeSeriesFileType.THERMAL_MODULATION,
                            study_path,
                            area_name,
                            group_name,
                        ).time_series
                        self._thermals[f"{group_name}-modulation"] = thermal_module

                # Get everything inside input/thermal/series/{area_name}
                prefix_path = (
                    study_path
                    / TimeSeriesFileType.THERMAL_SERIES_PREFIX.value.format(
                        area_id=area_name
                    )
                )
                groups = lister_dossiers(prefix_path)
                if self._directory_not_exists(study_path):
                    for group_name in groups:
                        thermal_series = TimeSeriesFile(
                            TimeSeriesFileType.THERMAL_DATA_SERIES,
                            study_path,
                            area_name,
                            group_name,
                        ).time_series
                        self._thermals[f"{group_name}-series"] = thermal_series
                        # bc_service: BaseStudyService = BindingConstraintLocalService(self.config, self.study_name)
                        # bc = bc_service.read_binding_constraint(area_name)
                        # self._areas[bc.id] = area
                        # link_service: BaseStudyService = LinkLocalService(self.config, self.study_name)
                        # se modelise par deux area et une capacite
                        # link = link_service.read_link(area_name)
                        # self._areas[link.id] = area
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")

        return areas
