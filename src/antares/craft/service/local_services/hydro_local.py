import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.service.base_services import BaseHydroService


class HydroLocalService(BaseHydroService):
    def __init__(self, config: LocalConfiguration, area_id: str):
        raise NotImplementedError()

    def get_maxpower(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    def get_reservoir(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    def get_inflow_pattern(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    def get_credit_modulations(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()

    def get_water_values(self, area_id: str) -> pd.DataFrame:
        raise NotImplementedError()
