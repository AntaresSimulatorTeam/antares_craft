from typing import Any

import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.model.renewable import RenewableCluster, RenewableClusterProperties
from antares.service.base_services import BaseRenewableService


class RenewableLocalService(BaseRenewableService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def update_renewable_properties(
        self,
        renewable_cluster: RenewableCluster,
        properties: RenewableClusterProperties,
    ) -> RenewableClusterProperties:
        raise NotImplementedError

    def get_renewable_matrix(
        self,
        renewable: RenewableCluster,
    ) -> pd.DataFrame:
        raise NotImplementedError
