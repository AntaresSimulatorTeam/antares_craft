from typing import Optional, Any

from antares.config.local_configuration import LocalConfiguration
from antares.model.binding_constraint import BindingConstraint
from antares.model.settings import StudySettings
from antares.service.base_services import BaseStudyService


class StudyLocalService(BaseStudyService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self._config = config
        self._study_name = study_name

    @property
    def study_id(self) -> str:
        return self._study_name

    @property
    def config(self) -> LocalConfiguration:
        return self._config

    def update_study_settings(self, settings: StudySettings) -> Optional[StudySettings]:
        raise NotImplementedError

    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        raise NotImplementedError

    def delete(self, children: bool) -> None:
        raise NotImplementedError
