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
import copy

from pathlib import Path
from typing import Any

import pandas as pd

from typing_extensions import override

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    STStorageConstraintCreationError,
    STStorageConstraintDeletionError,
    STStorageConstraintEditionError,
    STStoragePropertiesUpdateError,
)
from antares.craft.model.commons import STUDY_VERSION_8_8, STUDY_VERSION_9_2
from antares.craft.model.st_storage import (
    STStorage,
    STStorageAdditionalConstraint,
    STStorageAdditionalConstraintUpdate,
    STStorageMatrixName,
    STStorageProperties,
    STStoragePropertiesUpdate,
)
from antares.craft.service.base_services import BaseShortTermStorageService
from antares.craft.service.local_services.models.st_storage import (
    parse_st_storage_constraint_local,
    parse_st_storage_local,
    serialize_st_storage_constraint_local,
    serialize_st_storage_local,
    update_st_storage_constraint_local,
)
from antares.craft.service.local_services.services.utils import checks_matrix_dimensions
from antares.craft.tools.contents_tool import transform_name_to_id
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from antares.study.version import StudyVersion

MAPPING = {
    STStorageMatrixName.PMAX_INJECTION: TimeSeriesFileType.ST_STORAGE_PMAX_INJECTION,
    STStorageMatrixName.PMAX_WITHDRAWAL: TimeSeriesFileType.ST_STORAGE_PMAX_WITHDRAWAL,
    STStorageMatrixName.LOWER_CURVE_RULE: TimeSeriesFileType.ST_STORAGE_LOWER_RULE_CURVE,
    STStorageMatrixName.UPPER_RULE_CURVE: TimeSeriesFileType.ST_STORAGE_UPPER_RULE_CURVE,
    STStorageMatrixName.INFLOWS: TimeSeriesFileType.ST_STORAGE_INFLOWS,
    STStorageMatrixName.COST_INJECTION: TimeSeriesFileType.ST_STORAGE_COST_INJECTION,
    STStorageMatrixName.COST_WITHDRAWAL: TimeSeriesFileType.ST_STORAGE_COST_WITHDRAWAL,
    STStorageMatrixName.COST_LEVEL: TimeSeriesFileType.ST_STORAGE_COST_LEVEL,
    STStorageMatrixName.COST_VARIATION_INJECTION: TimeSeriesFileType.ST_STORAGE_COST_VARIATION_INJECTION,
    STStorageMatrixName.COST_VARIATION_WITHDRAWAL: TimeSeriesFileType.ST_STORAGE_COST_VARIATION_WITHDRAWAL,
}

FORBIDDEN_MATRICES_88 = {
    STStorageMatrixName.COST_INJECTION,
    STStorageMatrixName.COST_WITHDRAWAL,
    STStorageMatrixName.COST_LEVEL,
    STStorageMatrixName.COST_VARIATION_INJECTION,
    STStorageMatrixName.COST_VARIATION_WITHDRAWAL,
}

CONSTRAINTS_ERROR_MSG = "The short-term storage constraints only exists in v9.2+ studies"


class ShortTermStorageLocalService(BaseShortTermStorageService):
    def __init__(self, config: LocalConfiguration, study_name: str, study_version: StudyVersion, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        self.config = config
        self.study_name = study_name
        self.study_version = study_version

    def _get_ini_path(self, area_id: str) -> Path:
        return self.config.study_path / "input" / "st-storage" / "clusters" / area_id / "list.ini"

    def _check_matrix_allowed(self, ts_name: STStorageMatrixName) -> None:
        if self.study_version == STUDY_VERSION_8_8 and ts_name in FORBIDDEN_MATRICES_88:
            raise ValueError(f"The matrix {ts_name.value} is not available for study version 8.8")

    def read_ini(self, area_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_ini_path(area_id))

    def save_ini(self, content: dict[str, Any], area_id: str) -> None:
        IniWriter().write(content, self._get_ini_path(area_id))

    def _get_ini_constraints_path(self, area_id: str, storage_id: str) -> Path:
        return (
            self.config.study_path
            / "input"
            / "st-storage"
            / "constraints"
            / area_id
            / storage_id
            / "additional-constraints.ini"
        )

    def _read_ini_constraints(self, area_id: str, storage_id: str) -> dict[str, Any]:
        return IniReader().read(self._get_ini_constraints_path(area_id, storage_id))

    def _save_ini_constraints(self, content: dict[str, Any], area_id: str, storage_id: str) -> None:
        IniWriter().write(content, self._get_ini_constraints_path(area_id, storage_id))

    @override
    def read_st_storages(self) -> dict[str, dict[str, STStorage]]:
        st_storages: dict[str, dict[str, STStorage]] = {}
        cluster_path = self.config.study_path / "input" / "st-storage" / "clusters"
        if not cluster_path.exists():
            return {}

        constraints = {}
        if self.study_version >= STUDY_VERSION_9_2:
            constraints = self._read_constraints()

        for folder in cluster_path.iterdir():
            if folder.is_dir():
                area_id = folder.name

                storage_dict = self.read_ini(area_id)

                for storage_data in storage_dict.values():
                    storage_name = str(storage_data.pop("name"))
                    storage_properties = parse_st_storage_local(self.study_version, storage_data)
                    storage_id = transform_name_to_id(storage_name)
                    relative_constraints = constraints.get(area_id, {}).get(storage_id, {})
                    st_storage = STStorage(
                        storage_service=self,
                        area_id=area_id,
                        name=storage_name,
                        properties=storage_properties,
                        constraints=relative_constraints,
                    )
                    st_storages.setdefault(area_id, {})[storage_id] = st_storage

        return st_storages

    @override
    def set_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName, matrix: pd.DataFrame) -> None:
        self._check_matrix_allowed(ts_name)
        checks_matrix_dimensions(matrix, f"storage/{storage.area_id}/{storage.name}", ts_name.value)
        write_timeseries(self.config.study_path, matrix, MAPPING[ts_name], storage.area_id, storage.id)

    @override
    def get_storage_matrix(self, storage: STStorage, ts_name: STStorageMatrixName) -> pd.DataFrame:
        self._check_matrix_allowed(ts_name)
        return read_timeseries(MAPPING[ts_name], self.config.study_path, area_id=storage.area_id, cluster_id=storage.id)

    @override
    def update_st_storages_properties(
        self, new_properties: dict[STStorage, STStoragePropertiesUpdate]
    ) -> dict[STStorage, STStorageProperties]:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        memory_mapping = {}

        new_properties_dict: dict[STStorage, STStorageProperties] = {}
        cluster_name_to_object: dict[str, STStorage] = {}

        properties_by_areas: dict[str, dict[str, STStoragePropertiesUpdate]] = {}

        for sts, properties in new_properties.items():
            properties_by_areas.setdefault(sts.area_id, {})[sts.name] = properties
            cluster_name_to_object[sts.name] = sts

        for area_id, value in properties_by_areas.items():
            all_storage_name = set(value.keys())  # used to raise an Exception if a storage doesn't exist
            st_storage_dict = self.read_ini(area_id)
            for storage in st_storage_dict.values():
                storage_name = storage["name"]
                if storage_name in value:
                    all_storage_name.remove(storage_name)

                    # Update properties
                    upd_props_as_dict = serialize_st_storage_local(self.study_version, value[storage_name])
                    storage.update(upd_props_as_dict)

                    # Prepare the object to return
                    local_dict = copy.deepcopy(storage)
                    del local_dict["name"]
                    user_properties = parse_st_storage_local(self.study_version, local_dict)
                    new_properties_dict[cluster_name_to_object[storage_name]] = user_properties

            if len(all_storage_name) > 0:
                raise STStoragePropertiesUpdateError(
                    next(iter(all_storage_name)), area_id, "The storage does not exist"
                )

            memory_mapping[area_id] = st_storage_dict

        # Update ini files
        for area_id, ini_content in memory_mapping.items():
            self.save_ini(ini_content, area_id)

        return new_properties_dict

    def _read_constraints(self) -> dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]]:
        constraints: dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]] = {}

        folder_path = self.config.study_path / "input" / "st-storage" / "constraints"
        if not folder_path.exists():
            return {}
        for area_folder in folder_path.iterdir():
            area_id = area_folder.name
            for storage_folder in area_folder.iterdir():
                storage_id = storage_folder.name
                sts_constraints = self._read_constraints_for_a_storage(area_id, storage_id)
                constraints.setdefault(area_id, {})[storage_id] = sts_constraints

        return constraints

    def _read_constraints_for_a_storage(
        self, area_id: str, storage_id: str
    ) -> dict[str, STStorageAdditionalConstraint]:
        constraints = {}
        ini_content = self._read_ini_constraints(area_id, storage_id)
        for constraint_name, data in ini_content.items():
            args = {"name": constraint_name, **data}
            constraint = parse_st_storage_constraint_local(args)
            constraints[constraint.id] = constraint

        return constraints

    def _save_constraints(
        self, area_id: str, storage_id: str, constraints: dict[str, STStorageAdditionalConstraint]
    ) -> dict[str, STStorageAdditionalConstraint]:
        saved_constraints = {}
        ini_content = {}
        for constraint in constraints.values():
            content = serialize_st_storage_constraint_local(constraint)
            ini_content[constraint.name] = content
            # Round trip for validation
            saved_constraints[constraint.id] = parse_st_storage_constraint_local(content)

        # Save the data in the ini file
        self._save_ini_constraints(ini_content, area_id, storage_id)

        return saved_constraints

    @override
    def create_constraints(
        self, area_id: str, storage_id: str, constraints: list[STStorageAdditionalConstraint]
    ) -> list[STStorageAdditionalConstraint]:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(CONSTRAINTS_ERROR_MSG)

        existing_constraints = self._read_constraints_for_a_storage(area_id, storage_id)
        # Checks if the constraints don't already exist
        for constraint in constraints:
            if constraint.id in existing_constraints:
                raise STStorageConstraintCreationError(
                    self.study_name, area_id, storage_id, f"{constraint.id} already exists"
                )

        for constraint in constraints:
            existing_constraints[constraint.name] = constraint

        created_constraints = self._save_constraints(area_id, storage_id, existing_constraints)
        return list(created_constraints.values())

    @override
    def delete_constraints(self, area_id: str, storage_id: str, constraint_ids: list[str]) -> None:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(CONSTRAINTS_ERROR_MSG)

        matrix_ids_to_remove = set()

        existing_constraints = self._read_constraints_for_a_storage(area_id, storage_id)
        for constraint_id in constraint_ids:
            if constraint_id not in existing_constraints:
                raise STStorageConstraintDeletionError(
                    self.study_name, area_id, storage_id, f"The constraint {constraint_id} does not exist"
                )

            del existing_constraints[constraint_id]
            matrix_ids_to_remove.add(constraint_id)

        self._save_constraints(area_id, storage_id, existing_constraints)

        # Deletes the matrix
        for matrix_id in matrix_ids_to_remove:
            matrix_path = (
                self.config.study_path
                / "input"
                / "st-storage"
                / "constraints"
                / area_id
                / storage_id
                / f"rhs_{matrix_id}.txt"
            )
            matrix_path.unlink(missing_ok=True)

    @override
    def get_constraint_term(self, area_id: str, storage_id: str, constraint_id: str) -> pd.DataFrame:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(CONSTRAINTS_ERROR_MSG)

        ts = TimeSeriesFileType.ST_STORAGE_CONSTRAINT_TERM
        return read_timeseries(
            ts, self.config.study_path, area_id=area_id, constraint_id=constraint_id, cluster_id=storage_id
        )

    @override
    def set_constraint_term(self, area_id: str, storage_id: str, constraint_id: str, matrix: pd.DataFrame) -> None:
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(CONSTRAINTS_ERROR_MSG)

        ts = TimeSeriesFileType.ST_STORAGE_CONSTRAINT_TERM
        write_timeseries(self.config.study_path, matrix, ts, area_id, storage_id, constraint_id=constraint_id)

    @override
    def update_st_storages_constraints(
        self, new_constraints: dict[STStorage, dict[str, STStorageAdditionalConstraintUpdate]]
    ) -> dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]]:
        """
        We validate ALL objects before saving them.
        This way, if some data is invalid, we're not modifying the study partially only.
        """
        if self.study_version < STUDY_VERSION_9_2:
            raise ValueError(CONSTRAINTS_ERROR_MSG)

        memory_mapping: dict[str, dict[str, dict[str, STStorageAdditionalConstraint]]] = {}

        constraints_by_area_and_storage: dict[str, dict[str, dict[str, STStorageAdditionalConstraintUpdate]]] = {}

        for sts, constraints in new_constraints.items():
            constraints_by_area_and_storage.setdefault(sts.area_id, {})[sts.id] = constraints

        for area_id, value in constraints_by_area_and_storage.items():
            memory_mapping[area_id] = {}
            for storage_id, constraints in value.items():
                existing_constraints = self._read_constraints_for_a_storage(area_id, storage_id)
                memory_mapping[area_id][storage_id] = existing_constraints
                constraints_ids_to_update = set(constraints)  # used to raise an Exception if a constraint doesn't exist

                for constraint in existing_constraints.values():
                    c_id = constraint.id
                    if c_id in constraints_ids_to_update:
                        constraints_ids_to_update.remove(c_id)

                        # Update the constraint
                        new_constraint = update_st_storage_constraint_local(constraint, constraints[c_id])
                        memory_mapping[area_id][storage_id][new_constraint.id] = new_constraint

                if len(constraints_ids_to_update) > 0:
                    raise STStorageConstraintEditionError(
                        self.study_name, f"The constraint(s) {constraints_ids_to_update} do not exist"
                    )

        # Update ini files
        for area_id, v in memory_mapping.items():
            for storage_id, modified_constraints in v.items():
                self._save_constraints(area_id, storage_id, modified_constraints)

        return memory_mapping
