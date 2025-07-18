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

from typing import Any

import pandas as pd

from typing_extensions import override

from antares.craft import XpansionCandidate, XpansionCandidateUpdate, XpansionConstraint, XpansionConstraintUpdate
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import (
    XpansionCandidateCoherenceError,
    XpansionCandidateCreationError,
    XpansionCandidateEditionError,
    XpansionConstraintCreationError,
    XpansionConstraintsDeletionError,
    XpansionMatrixDeletionError,
    XpansionMatrixReadingError,
)
from antares.craft.model.xpansion.candidate import XpansionLinkProfile, update_candidate
from antares.craft.model.xpansion.settings import XpansionSettings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration, XpansionMatrix
from antares.craft.service.base_services import BaseXpansionService
from antares.craft.service.local_services.models.xpansion import (
    parse_xpansion_candidate_local,
    parse_xpansion_constraints_local,
    parse_xpansion_sensitivity_local,
    parse_xpansion_settings_local,
    serialize_xpansion_candidate_local,
    serialize_xpansion_constraints_local,
    serialize_xpansion_settings_local,
)
from antares.craft.tools.matrix_tool import read_timeseries, write_timeseries
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.serde_local.ini_writer import IniWriter
from antares.craft.tools.serde_local.json import from_json
from antares.craft.tools.time_series_tool import TimeSeriesFileType

FILE_MAPPING: dict[XpansionMatrix, tuple[str, TimeSeriesFileType]] = {
    XpansionMatrix.WEIGHTS: ("weights", TimeSeriesFileType.XPANSION_WEIGHT),
    XpansionMatrix.CAPACITIES: ("capa", TimeSeriesFileType.XPANSION_CAPACITY),
}


class XpansionLocalService(BaseXpansionService):
    def __init__(self, config: LocalConfiguration, study_name: str):
        self.config = config
        self.study_name = study_name
        self._xpansion_path = self.config.study_path / "user" / "expansion"

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        if not self._xpansion_path.exists():
            return None
        # Settings
        settings = parse_xpansion_settings_local(self._read_settings()["settings"])
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
        sensitivity = None
        sensitivity_content = self._read_sensitivity()
        if sensitivity_content:
            sensitivity = parse_xpansion_sensitivity_local(sensitivity_content)
        return XpansionConfiguration(
            self, settings=settings, candidates=candidates, constraints=constraints, sensitivity=sensitivity
        )

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        for folder in ["capa", "constraints", "weights", "sensitivity"]:
            (self._xpansion_path / folder).mkdir(parents=True)
        with open(self._xpansion_path / "sensitivity" / "sensitivity_in.json", "w") as f:
            f.write("{}")
        (self._xpansion_path / "candidates.ini").touch()
        settings = XpansionSettings()
        ini_content = serialize_xpansion_settings_local(settings)
        with open(self._xpansion_path / "settings.ini", "w") as f:
            f.writelines(f"{k}={v}\n" for k, v in ini_content.items())
        return XpansionConfiguration(self, settings)

    @override
    def delete(self) -> None:
        shutil.rmtree(self._xpansion_path)

    @override
    def get_matrix(self, file_name: str, file_type: XpansionMatrix) -> pd.DataFrame:
        try:
            return read_timeseries(FILE_MAPPING[file_type][1], self.config.study_path, file_name=file_name)
        except FileNotFoundError:
            raise XpansionMatrixReadingError(self.study_name, file_name, "The file does not exist")

    @override
    def delete_matrix(self, file_name: str, file_type: XpansionMatrix) -> None:
        file_path = self._xpansion_path / FILE_MAPPING[file_type][0] / file_name
        if not file_path.exists():
            raise XpansionMatrixDeletionError(self.study_name, file_name, "The file does not exist")
        file_path.unlink()

    @override
    def set_matrix(self, file_name: str, series: pd.DataFrame, file_type: XpansionMatrix) -> None:
        write_timeseries(self.config.study_path, series, FILE_MAPPING[file_type][1], file_name=file_name)

    @override
    def create_candidate(self, candidate: XpansionCandidate) -> XpansionCandidate:
        self._checks_candidate_coherence(candidate)
        ini_content = self._read_candidates()
        for key, value in ini_content.items():
            if candidate.name == value["name"]:
                raise XpansionCandidateCreationError(self.study_name, candidate.name, "Candidate already exists")

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

        raise XpansionCandidateEditionError(self.study_name, name, "Candidate does not exist")

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
                            self.study_name, candidate.name, f"The key {profile.value} does not exist"
                        )
                    del value[profile.value]

                user_class = parse_xpansion_candidate_local(value)

                # Saves the content
                self._save_candidates(ini_content)
                return user_class
        raise XpansionCandidateEditionError(self.study_name, candidate.name, "Candidate does not exist")

    @override
    def create_constraint(self, constraint: XpansionConstraint, file_name: str) -> XpansionConstraint:
        existing_constraints = self._read_constraints(file_name)
        if constraint.name in existing_constraints:
            raise XpansionConstraintCreationError(
                self.study_name, constraint.name, file_name, "Constraint already exists"
            )
        existing_constraints[constraint.name] = constraint
        # Saves the content
        self._write_constraints(file_name, existing_constraints)
        # Round-trip to validate the data
        return parse_xpansion_constraints_local(serialize_xpansion_constraints_local({"": constraint}))[""]

    @override
    def update_constraint(self, name: str, constraint: XpansionConstraintUpdate, file_name: str) -> XpansionConstraint:
        raise NotImplementedError()

    @override
    def delete_constraints(self, names: list[str], file_name: str) -> None:
        existing_constraints = self._read_constraints(file_name)
        for name in names:
            if name not in existing_constraints:
                raise XpansionConstraintsDeletionError(self.study_name, [name], file_name, "Constraint does not exist")
            del existing_constraints[name]
        # Saves the content
        self._write_constraints(file_name, existing_constraints)

    def _read_settings(self) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "settings.ini")

    def _read_candidates(self) -> dict[str, Any]:
        return IniReader().read(self._xpansion_path / "candidates.ini")

    def _save_candidates(self, content: dict[str, Any]) -> None:
        IniWriter().write(content, self._xpansion_path / "candidates.ini")

    def _read_constraints(self, file_name: str) -> dict[str, XpansionConstraint]:
        return parse_xpansion_constraints_local(IniReader().read(self._xpansion_path / "constraints" / file_name))

    def _write_constraints(self, file_name: str, constraints: dict[str, XpansionConstraint]) -> None:
        ini_content = serialize_xpansion_constraints_local(constraints)
        IniWriter().write(ini_content, self._xpansion_path / "constraints" / file_name)

    def _read_sensitivity(self) -> dict[str, Any]:
        file_path = self._xpansion_path / "sensitivity" / "sensitivity_in.json"
        if file_path.exists():
            return from_json(file_path.read_text())
        return {}

    def _checks_candidate_coherence(self, candidate: XpansionCandidate) -> None:
        area_from, area_to = sorted([candidate.area_from, candidate.area_to])
        if not (self.config.study_path / "input" / "links" / area_from / f"{area_to}_parameters.txt").exists():
            raise XpansionCandidateCoherenceError(
                self.study_name, candidate.name, f"Link between {area_from} and {area_to} does not exist"
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
                raise XpansionCandidateCoherenceError(self.study_name, candidate.name, f"File {file} does not exist")
