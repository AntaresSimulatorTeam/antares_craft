from typing import Any

from antares.config.local_configuration import LocalConfiguration
from antares.model.st_storage import STStorage, STStorageProperties
from antares.service.base_services import BaseShortTermStorageService


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_st_storage_properties(
        self, st_storage: STStorage, properties: STStorageProperties
    ) -> STStorageProperties:
        raise NotImplementedError
