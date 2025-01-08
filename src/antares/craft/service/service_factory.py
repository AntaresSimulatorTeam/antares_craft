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

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.config.base_configuration import BaseConfiguration
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.service.api_services.area_api import AreaApiService
from antares.craft.service.api_services.binding_constraint_api import BindingConstraintApiService
from antares.craft.service.api_services.link_api import LinkApiService
from antares.craft.service.api_services.output_api import OutputApiService
from antares.craft.service.api_services.renewable_api import RenewableApiService
from antares.craft.service.api_services.run_api import RunApiService
from antares.craft.service.api_services.st_storage_api import ShortTermStorageApiService
from antares.craft.service.api_services.study_api import StudyApiService
from antares.craft.service.api_services.thermal_api import ThermalApiService
from antares.craft.service.base_services import (
    BaseAreaService,
    BaseBindingConstraintService,
    BaseLinkService,
    BaseOutputService,
    BaseRenewableService,
    BaseRunService,
    BaseShortTermStorageService,
    BaseStudyService,
    BaseThermalService,
)
from antares.craft.service.local_services.area_local import AreaLocalService
from antares.craft.service.local_services.binding_constraint_local import BindingConstraintLocalService
from antares.craft.service.local_services.link_local import LinkLocalService
from antares.craft.service.local_services.output_local import OutputLocalService
from antares.craft.service.local_services.renewable_local import RenewableLocalService
from antares.craft.service.local_services.run_local import RunLocalService
from antares.craft.service.local_services.st_storage_local import ShortTermStorageLocalService
from antares.craft.service.local_services.study_local import StudyLocalService
from antares.craft.service.local_services.thermal_local import ThermalLocalService

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
        study_service: BaseStudyService
        if isinstance(self.config, APIconf):
            study_service = StudyApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            study_service = StudyLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")

        study_service.set_output_service(self.create_output_service())
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

    def create_run_service(self) -> BaseRunService:
        if isinstance(self.config, APIconf):
            run_service: BaseRunService = RunApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            run_service = RunLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return run_service

    def create_output_service(self) -> BaseOutputService:
        if isinstance(self.config, APIconf):
            output_service: BaseOutputService = OutputApiService(self.config, self.study_id)
        elif isinstance(self.config, LocalConfiguration):
            output_service = OutputLocalService(self.config, self.study_name)
        else:
            raise TypeError(f"{ERROR_MESSAGE}{repr(self.config)}")
        return output_service
