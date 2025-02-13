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
from abc import ABC, abstractmethod

from antares.craft.service.base_services import (
    BaseAreaService,
    BaseBindingConstraintService,
    BaseHydroService,
    BaseLinkService,
    BaseOutputService,
    BaseRenewableService,
    BaseRunService,
    BaseShortTermStorageService,
    BaseStudyService,
    BaseStudySettingsService,
    BaseThermalService,
)

ERROR_MESSAGE = "Unsupported configuration type: "


class ServiceFactory(ABC):
    """
    Service factory API
    """

    @abstractmethod
    def create_area_service(self) -> BaseAreaService:
        ...

    @abstractmethod
    def create_link_service(self) -> BaseLinkService:
        ...

    @abstractmethod
    def create_thermal_service(self) -> BaseThermalService:
        ...

    @abstractmethod
    def create_binding_constraints_service(self) -> BaseBindingConstraintService:
        ...

    @abstractmethod
    def create_study_service(self) -> BaseStudyService:
        ...

    @abstractmethod
    def create_renewable_service(self) -> BaseRenewableService:
        ...

    @abstractmethod
    def create_st_storage_service(self) -> BaseShortTermStorageService:
        ...

    @abstractmethod
    def create_run_service(self) -> BaseRunService:
        ...

    @abstractmethod
    def create_output_service(self) -> BaseOutputService:
        ...

    @abstractmethod
    def create_settings_service(self) -> BaseStudySettingsService:
        ...

    @abstractmethod
    def create_hydro_service(self) -> BaseHydroService:
        ...



