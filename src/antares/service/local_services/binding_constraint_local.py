from typing import Optional, List, Any

import pandas as pd

from antares.config.local_configuration import LocalConfiguration
from antares.model.binding_constraint import (
    BindingConstraintProperties,
    ConstraintTerm,
    BindingConstraint,
    ConstraintMatrixName,
)
from antares.service.base_services import BaseBindingConstraintService


class BindingConstraintLocalService(BaseBindingConstraintService):
    def __init__(self, config: LocalConfiguration, study_name: str, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name

    def create_binding_constraint(
        self,
        name: str,
        properties: Optional[BindingConstraintProperties] = None,
        terms: Optional[List[ConstraintTerm]] = None,
        less_term_matrix: Optional[pd.DataFrame] = None,
        equal_term_matrix: Optional[pd.DataFrame] = None,
        greater_term_matrix: Optional[pd.DataFrame] = None,
    ) -> BindingConstraint:
        raise NotImplementedError

    def add_constraint_terms(self, constraint: BindingConstraint, terms: List[ConstraintTerm]) -> List[ConstraintTerm]:
        raise NotImplementedError

    def delete_binding_constraint_term(self, constraint_id: str, term_id: str) -> None:
        raise NotImplementedError

    def update_binding_constraint_properties(
        self,
        binding_constraint: BindingConstraint,
        properties: BindingConstraintProperties,
    ) -> BindingConstraintProperties:
        raise NotImplementedError

    def get_constraint_matrix(self, constraint: BindingConstraint, matrix_name: ConstraintMatrixName) -> pd.DataFrame:
        raise NotImplementedError

    def update_constraint_matrix(
        self,
        constraint: BindingConstraint,
        matrix_name: ConstraintMatrixName,
        matrix: pd.DataFrame,
    ) -> None:
        raise NotImplementedError

    def read_binding_constraint(
        self,
        constraint: BindingConstraint,
        matrix_name: ConstraintMatrixName,
        matrix: pd.DataFrame,
    ) -> None:
        raise NotImplementedError
