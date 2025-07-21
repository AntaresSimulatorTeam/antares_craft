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
import shutil

from dataclasses import replace
from pathlib import Path
from typing import Any

import pandas as pd

from typing_extensions import override

from antares.craft import (
    XpansionCandidate,
    XpansionCandidateUpdate,
    XpansionConstraint,
    XpansionConstraintUpdate,
    XpansionSensitivity,
    XpansionSensitivityUpdate,
)
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    XpansionCandidateCoherenceError,
    XpansionCandidateCreationError,
    XpansionCandidateDeletionError,
    XpansionCandidateEditionError,
    XpansionConstraintCreationError,
    XpansionConstraintsDeletionError,
    XpansionConstraintsEditionError,
    XpansionFileDeletionError,
    XpansionMatrixReadingError,
    XpansionSettingsEditionError,
)
from antares.craft.model.xpansion.candidate import XpansionLinkProfile, update_candidate
from antares.craft.model.xpansion.constraint import update_constraint
from antares.craft.model.xpansion.sensitivity import update_xpansion_sensitivity
from antares.craft.model.xpansion.settings import XpansionSettings, XpansionSettingsUpdate, update_xpansion_settings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration, XpansionMatrix
from antares.craft.service.base_services import BaseXpansionService
from antares.craft.service.local_services.models.xpansion import (
    parse_xpansion_candidate_local,
    parse_xpansion_constraints_local,
    parse_xpansion_sensitivity_local,
    parse_xpansion_settings_local,
    serialize_xpansion_candidate_local,
    serialize_xpansion_constraints_local,
    serialize_xpansion_sensitivity_local,
    serialize_xpansion_settings_local,
)
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.serde_local.json import from_json, to_json_string
from antares.craft.tools.time_series_tool import TimeSeriesFileType

FILE_MAPPING: dict[XpansionMatrix, tuple[str, TimeSeriesFileType]] = {
    XpansionMatrix.WEIGHTS: ("weights", TimeSeriesFileType.XPANSION_WEIGHT),
    XpansionMatrix.CAPACITIES: ("capa", TimeSeriesFileType.XPANSION_CAPACITY),
}


class XpansionLocalService(BaseXpansionService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self._study_name = study_name
        self._xpansion_path = self.config.study_path / "user" / "expansion"

    @property
    @override
    def study_id(self) -> str:
        return self._study_name

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        if not self._xpansion_path.exists():
            return None
        # Settings
        settings = self._read_settings()
        # Candidates
        candidates = {}
        ini_candidates = self._read_candidates()
        for values in ini_candidates.values():
            cdt = parse_xpansion_candidate_local(values)
            candidates[cdt.name] = cdt
        # Constraints
        constraints = {}
        file_name = settings.additional_constraints
        if file_name:
            constraints = self._read_constraints(file_name)
        # Sensitivity
        sensitivity = self._read_sensitivity()
        return XpansionConfiguration(
            self, settings=settings, candidates=candidates, constraints=constraints, sensitivity=sensitivity
        )

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        for folder in ["capa", "constraints", "weights", "sensitivity"]:
            (self._xpansion_path / folder).mkdir(parents=True)
        sensitivity = XpansionSensitivity()
        self._write_sensitivity(sensitivity)
        (self._xpansion_path / "candidates.ini").touch()
        settings = XpansionSettings()
        self._write_settings(settings)
        return XpansionConfiguration(self, settings=settings, sensitivity=sensitivity)

    @override
    def delete(self) -> None:
        shutil.rmtree(self._xpansion_path)

    @override
    def get_matrix(self, file_name: str, file_type: XpansionMatrix) -> pd.DataFrame:
        try:
            return read_timeseries(FILE_MAPPING[file_type][1], self.config.study_path, file_name=file_name)
        except FileNotFoundError:
            raise XpansionMatrixReadingError(self._study_name, file_name, "The file does not exist")

    @override
    def delete_matrix(self, file_name: str, file_type: XpansionMatrix) -> None:
        file_path = self._xpansion_path / FILE_MAPPING[file_type][0] / file_name
        self._delete_matrix(file_name, file_path)

    @override
    def set_matrix(self, file_name: str, series: pd.DataFrame, file_type: XpansionMatrix) -> None:
        write_timeseries(self.config.study_path, series, FILE_MAPPING[file_type][1], file_name=file_name)

    @override
    def create_candidate(self, candidate: XpansionCandidate) -> XpansionCandidate:
        self._checks_candidate_coherence(candidate)
        ini_content = self._read_candidates()
        for key, value in ini_content.items():
            if candidate.name == value["name"]:
                raise XpansionCandidateCreationError(self._study_name, candidate.name, "Candidate already exists")

        # Round-trip to validate data
        local_content = serialize_xpansion_candidate_local(candidate)
        user_class = parse_xpansion_candidate_local(local_content)

        # Saves the content
        ini_content[str(len(ini_content) + 1)] = local_content  # ini key starts at 1
        self._save_candidates(ini_content)
        return user_class

    @override
    def update_candidate(self, name: str, candidate: XpansionCandidateUpdate) -> XpansionCandidate:
        ini_content = self._read_candidates()
        for key, value in ini_content.items():
            if name == value["name"]:
                # Update properties
                current_candidate = parse_xpansion_candidate_local(value)
                updated_candidate = update_candidate(current_candidate, candidate)

                # Round-trip to validate data
                new_content = serialize_xpansion_candidate_local(updated_candidate)
                user_class = parse_xpansion_candidate_local(new_content)
                self._checks_candidate_coherence(user_class)

                # Saves the content
                ini_content[key] = new_content
                self._save_candidates(ini_content)

                return user_class

        raise XpansionCandidateEditionError(self._study_name, name, "Candidate does not exist")

    @override
    def delete_candidates(self, names: set[str]) -> None:
        ini_content = self._read_candidates()
        keys_to_delete = []
        for key, value in ini_content.items():
            if value["name"] in names:
                keys_to_delete.append(key)
                names.remove(value["name"])

        if names:
            raise XpansionCandidateDeletionError(self._study_name, names, "They do not exist")

        # Saves the content
        for key in keys_to_delete:
            del ini_content[key]
        self._save_candidates(ini_content)

    @override
    def remove_links_profile_from_candidate(
        self, candidate: XpansionCandidate, profiles: list[XpansionLinkProfile]
    ) -> XpansionCandidate:
        ini_content = self._read_candidates()
        for key, value in ini_content.items():
            if candidate.name == value["name"]:
                # Update properties
                for profile in profiles:
                    if profile.value not in value:
                        raise XpansionCandidateEditionError(
                            self._study_name, candidate.name, f"The key {profile.value} does not exist"
                        )
                    del value[profile.value]

                user_class = parse_xpansion_candidate_local(value)

                # Saves the content
                self._save_candidates(ini_content)
                return user_class
        raise XpansionCandidateEditionError(self._study_name, candidate.name, "Candidate does not exist")

    @override
    def create_constraint(self, constraint: XpansionConstraint, file_name: str) -> XpansionConstraint:
        existing_constraints = self._read_constraints(file_name)
        if constraint.name in existing_constraints:
            raise XpansionConstraintCreationError(
                self._study_name, constraint.name, file_name, "Constraint already exists"
            )
        existing_constraints[constraint.name] = constraint
        # Saves the content
        self._write_constraints(file_name, existing_constraints)
        # Round-trip to validate the data
        return parse_xpansion_constraints_local(serialize_xpansion_constraints_local({"": constraint}))[constraint.name]

    @override
    def update_constraint(self, name: str, constraint: XpansionConstraintUpdate, file_name: str) -> XpansionConstraint:
        existing_constraints = self._read_constraints(file_name)
        if name not in existing_constraints:
            raise XpansionConstraintsEditionError(self._study_name, name, file_name, "Constraint does not exist")
        new_constraint = update_constraint(existing_constraints[name], constraint)
        if new_constraint.name != name:
            # We're renaming the constraint
            del existing_constraints[name]
        existing_constraints[new_constraint.name] = new_constraint
        # Saves the content
        self._write_constraints(file_name, existing_constraints)
        # Round-trip to validate the data
        return parse_xpansion_constraints_local(serialize_xpansion_constraints_local({"": new_constraint}))[
            new_constraint.name
        ]

    @override
    def delete_constraints(self, names: list[str], file_name: str) -> None:
        existing_constraints = self._read_constraints(file_name)
        for name in names:
            if name not in existing_constraints:
                raise XpansionConstraintsDeletionError(self._study_name, [name], file_name, "Constraint does not exist")
            del existing_constraints[name]
        # Saves the content
        self._write_constraints(file_name, existing_constraints)

    @override
    def delete_constraints_file(self, file_name: str) -> None:
        file_path = self._xpansion_path / "constraints" / file_name
        self._delete_matrix(file_name, file_path)

    @override
    def update_settings(self, settings: XpansionSettingsUpdate, current_settings: XpansionSettings) -> XpansionSettings:
        new_settings = update_xpansion_settings(current_settings, settings)
        self._check_settings_coherence(new_settings)
        self._write_settings(new_settings)
        return new_settings

    @override
    def remove_constraints_and_or_weights_from_settings(
        self, constraint: bool, weight: bool, settings: XpansionSettings
    ) -> XpansionSettings:
        if constraint:
            settings = replace(settings, additional_constraints=None)
        if weight:
            settings = replace(settings, yearly_weights=None)
        self._write_settings(settings)
        return settings

    @override
    def update_sensitivity(
        self,
        sensitivity: XpansionSensitivityUpdate,
        current_settings: XpansionSettings,
        current_sensitivity: XpansionSensitivity,
    ) -> XpansionSensitivity:
        new_sensitivity = update_xpansion_sensitivity(current_sensitivity, sensitivity)
        self._write_sensitivity(new_sensitivity)
        return new_sensitivity

    def _read_settings(self) -> XpansionSettings:
        ini_content = IniReader().read(self._xpansion_path / "settings.ini")["settings"]
        return parse_xpansion_settings_local(ini_content)

    def _read_candidates(self) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "candidates.ini")

    def _save_candidates(self, content: dict[str, Any]) -> None:
        IniWriter().write(content, self._xpansion_path / "candidates.ini")

    def _read_constraints(self, file_name: str) -> dict[str, XpansionConstraint]:
        return parse_xpansion_constraints_local(IniReader().read(self._xpansion_path / "constraints" / file_name))

    def _write_constraints(self, file_name: str, constraints: dict[str, XpansionConstraint]) -> None:
        ini_content = serialize_xpansion_constraints_local(constraints)
        IniWriter().write(ini_content, self._xpansion_path / "constraints" / file_name)

    def _read_sensitivity(self) -> XpansionSensitivity:
        file_path = self._xpansion_path / "sensitivity" / "sensitivity_in.json"
        if file_path.exists():
            return parse_xpansion_sensitivity_local(from_json(file_path.read_text()))
        return XpansionSensitivity()

    def _checks_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        area_from, area_to = sorted([candidate.area_from, candidate.area_to])
        if not (self.config.study_path / "input" / "links" / area_from / f"{area_to}_parameters.txt").exists():
            raise XpansionCandidateCoherenceError(
                self._study_name, candidate.name, f"Link between {area_from} and {area_to} does not exist"
            )

        files_to_check = []
        for attr in [
            "direct_link_profile",
            "indirect_link_profile",
            "already_installed_direct_link_profile",
            "already_installed_indirect_link_profile",
        ]:
            capa_file = getattr(candidate, attr)
            if capa_file is not None:
                files_to_check.append(capa_file)
        for file in files_to_check:
            if not (self._xpansion_path / "capa" / file).exists():
                raise XpansionCandidateCoherenceError(self._study_name, candidate.name, f"File {file} does not exist")

    def _delete_matrix(self, file_name: str, file_path: Path) -> None:
        if not file_path.exists():
            raise XpansionFileDeletionError(self._study_name, file_name, "The file does not exist")
        file_path.unlink()

    def _write_settings(self, settings: XpansionSettings) -> None:
        ini_content = serialize_xpansion_settings_local(settings)
        with open(self._xpansion_path / "settings.ini", "w") as f:
            f.writelines(f"{k}={v}\n" for k, v in ini_content.items())

    def _check_settings_coherence(self, settings: XpansionSettings) -> None:
        if constraint := settings.additional_constraints:
            if not (self._xpansion_path / "constraints" / constraint).exists():
                raise XpansionSettingsEditionError(self._study_name, f"The file {constraint} does not exist")
        if weight := settings.yearly_weights:
            if not (self._xpansion_path / "weights" / weight).exists():
                raise XpansionSettingsEditionError(self._study_name, f"The file {weight} does not exist")

    def _write_sensitivity(self, sensitivity: XpansionSensitivity) -> None:
        content = serialize_xpansion_sensitivity_local(sensitivity)
        with open(self._xpansion_path / "sensitivity" / "sensitivity_in.json", "w") as f:
            f.write(to_json_string(content))
