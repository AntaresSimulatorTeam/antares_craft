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
import io

from dataclasses import replace

import pandas as pd

from typing_extensions import override

from antares.craft import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    XpansionCandidateCreationError,
    XpansionCandidateDeletionError,
    XpansionCandidateEditionError,
    XpansionConfigurationCreationError,
    XpansionConfigurationDeletionError,
    XpansionConfigurationReadingError,
    XpansionConstraintCreationError,
    XpansionConstraintsDeletionError,
    XpansionConstraintsEditionError,
    XpansionFileDeletionError,
    XpansionMatrixEditionError,
    XpansionMatrixReadingError,
    XpansionSettingsEditionError,
)
from antares.craft.model.xpansion.candidate import (
    XpansionCandidate,
    XpansionCandidateUpdate,
    XpansionLinkProfile,
    update_candidate,
)
from antares.craft.model.xpansion.constraint import XpansionConstraint, XpansionConstraintUpdate, update_constraint
from antares.craft.model.xpansion.sensitivity import (
    XpansionSensitivity,
    XpansionSensitivityUpdate,
    update_xpansion_sensitivity,
)
from antares.craft.model.xpansion.settings import XpansionSettings, XpansionSettingsUpdate, update_xpansion_settings
from antares.craft.model.xpansion.xpansion_configuration import XpansionConfiguration, XpansionMatrix
from antares.craft.service.api_services.models.xpansion import (
    parse_xpansion_candidate_api,
    parse_xpansion_constraint_api,
    parse_xpansion_constraints_api,
    parse_xpansion_settings_api,
    serialize_xpansion_candidate_api,
    serialize_xpansion_constraint_api,
    serialize_xpansion_constraints_api,
    serialize_xpansion_settings_api,
)
from antares.craft.service.api_services.utils import get_matrix, update_series
from antares.craft.service.base_services import BaseXpansionService

FILE_MAPPING: dict[XpansionMatrix, str] = {XpansionMatrix.WEIGHTS: "weights", XpansionMatrix.CAPACITIES: "capa"}


class XpansionAPIService(BaseXpansionService):
    def __init__(self, config: APIconf, study_id: str):
        super().__init__()
        self.config = config
        self._study_id = study_id
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._expansion_url = f"{self._base_url}/studies/{study_id}/extensions/xpansion"

    @property
    @override
    def study_id(self) -> str:
        return self._study_id

    @override
    def read_xpansion_configuration(self) -> XpansionConfiguration | None:
        # Checks the settings. If we have a 404 Exception, it means we don't have any Xpansion configuration
        try:
            settings, sensitivity = self._read_settings_and_sensitivity()
        except APIError:
            return None
        try:
            # Candidates
            candidates = self._read_candidates()
            # Constraints
            constraints = {}
            if settings.additional_constraints:
                constraints = self._read_constraints(settings.additional_constraints)
            return XpansionConfiguration(
                xpansion_service=self,
                settings=settings,
                sensitivity=sensitivity,
                candidates=candidates,
                constraints=constraints,
            )
        except APIError as e:
            raise XpansionConfigurationReadingError(self._study_id, e.message) from e

    @override
    def create_xpansion_configuration(self) -> XpansionConfiguration:
        try:
            self._wrapper.post(f"{self._expansion_url}/settings")
            settings, sensitivity = self._read_settings_and_sensitivity()
            return XpansionConfiguration(xpansion_service=self, settings=settings, sensitivity=sensitivity)
        except APIError as e:
            raise XpansionConfigurationCreationError(self._study_id, e.message) from e

    @override
    def delete(self) -> None:
        try:
            self._wrapper.delete(self._expansion_url)
        except APIError as e:
            raise XpansionConfigurationDeletionError(self._study_id, e.message) from e

    @override
    def get_matrix(self, file_name: str, file_type: XpansionMatrix) -> pd.DataFrame:
        series_path = f"user/expansion/{FILE_MAPPING[file_type]}/{file_name}"
        try:
            return get_matrix(self._base_url, self._study_id, self._wrapper, series_path)
        except APIError as e:
            raise XpansionMatrixReadingError(self._study_id, file_name, e.message) from e

    @override
    def delete_matrix(self, file_name: str, file_type: XpansionMatrix) -> None:
        url = f"{self._expansion_url}/resources/{file_type.value}/{file_name}"
        self._delete_matrix(file_name, url)

    @override
    def set_matrix(self, file_name: str, series: pd.DataFrame, file_type: XpansionMatrix) -> None:
        series_path = f"user/expansion/{FILE_MAPPING[file_type]}/{file_name}"
        try:
            update_series(self._base_url, self._study_id, self._wrapper, series, series_path)
        except APIError:
            # Perhaps the file didn't exist, we should try to create it.
            url = f"{self._expansion_url}/resources/{file_type.value}"
            try:
                buffer = io.StringIO()
                series.to_csv(buffer, sep="\t", header=False, index=False)
                self._wrapper.post(url, files={"file": (file_name, buffer.getvalue())})
            except APIError as e:
                raise XpansionMatrixEditionError(self._study_id, file_name, e.message) from e

    @override
    def create_candidate(self, candidate: XpansionCandidate) -> XpansionCandidate:
        url = f"{self._expansion_url}/candidates"
        try:
            body = serialize_xpansion_candidate_api(candidate)
            response = self._wrapper.post(url, json=body).json()
            return parse_xpansion_candidate_api(response)
        except APIError as e:
            raise XpansionCandidateCreationError(self._study_id, candidate.name, e.message) from e

    @override
    def update_candidate(self, name: str, candidate: XpansionCandidateUpdate) -> XpansionCandidate:
        url = f"{self._expansion_url}/candidates/{name}"
        try:
            # Update properties
            current_candidate = self._read_candidates()[name]
            updated_candidate = update_candidate(current_candidate, candidate)

            # Round-trip to validate data
            new_content = serialize_xpansion_candidate_api(updated_candidate)

            # Saves the content and parse the endpoint response
            response = self._wrapper.put(url, json=new_content).json()
            return parse_xpansion_candidate_api(response)

        except APIError as e:
            raise XpansionCandidateEditionError(self._study_id, name, e.message) from e

    @override
    def delete_candidates(self, names: set[str]) -> None:
        try:
            for name in names:
                url = f"{self._expansion_url}/candidates/{name}"
                self._wrapper.delete(url)

        except APIError as e:
            raise XpansionCandidateDeletionError(self._study_id, names, e.message) from e

    @override
    def remove_links_profile_from_candidate(
        self, candidate: XpansionCandidate, profiles: list[XpansionLinkProfile]
    ) -> XpansionCandidate:
        url = f"{self._expansion_url}/candidates/{candidate.name}"
        try:
            # Update properties
            body = serialize_xpansion_candidate_api(candidate)
            for profile in profiles:
                body[profile.value] = None

            # Saves the content
            self._wrapper.put(url, json=body)
            # Fetch the result
            response = self._wrapper.get(url).json()
            return parse_xpansion_candidate_api(response)

        except APIError as e:
            raise XpansionCandidateEditionError(self._study_id, candidate.name, e.message) from e

    @override
    def create_constraint(self, constraint: XpansionConstraint, file_name: str) -> XpansionConstraint:
        try:
            existing_constraints = self._read_constraints(file_name)
            existing_constraints[constraint.name] = constraint
        except APIError:
            # Happens if the file doesn't exist.
            existing_constraints = {constraint.name: constraint}

        try:
            self._serialize_constraints(file_name, existing_constraints)
        except APIError:
            # Happens if the file doesn't exist. We should create it
            try:
                url = f"{self._expansion_url}/resources/constraints"
                api_content = serialize_xpansion_constraints_api({"": constraint})
                self._wrapper.post(url, files={"file": (file_name, api_content)})
            except APIError as e:
                raise XpansionConstraintCreationError(self._study_id, constraint.name, file_name, e.message) from e

        # Round-trip to validate the data
        user_class = parse_xpansion_constraint_api(serialize_xpansion_constraint_api(constraint))
        return user_class

    @override
    def update_constraint(self, name: str, constraint: XpansionConstraintUpdate, file_name: str) -> XpansionConstraint:
        existing_constraints = self._read_constraints(file_name)
        new_constraint = update_constraint(existing_constraints[name], constraint)
        if new_constraint.name != name:
            # We're renaming the constraint
            del existing_constraints[name]
        existing_constraints[new_constraint.name] = new_constraint
        try:
            self._serialize_constraints(file_name, existing_constraints)
            return new_constraint

        except APIError as e:
            raise XpansionConstraintsEditionError(self._study_id, name, file_name, e.message) from e

    @override
    def delete_constraints(self, names: list[str], file_name: str) -> None:
        existing_constraints = self._read_constraints(file_name)
        for name in names:
            del existing_constraints[name]
        try:
            self._serialize_constraints(file_name, existing_constraints)

        except APIError as e:
            raise XpansionConstraintsDeletionError(self._study_id, names, file_name, e.message) from e

    @override
    def delete_constraints_file(self, file_name: str) -> None:
        url = f"{self._expansion_url}/resources/constraints/{file_name}"
        self._delete_matrix(file_name, url)

    @override
    def update_settings(self, settings: XpansionSettingsUpdate, current_settings: XpansionSettings) -> XpansionSettings:
        # We have to send `yearly-weights` and `additional-constraints` fields to the Web API otherwise it deletes them.
        new_settings = update_xpansion_settings(current_settings, settings)
        return self._update_settings(new_settings, None)[0]

    @override
    def remove_constraints_and_or_weights_from_settings(
        self, constraint: bool, weight: bool, settings: XpansionSettings
    ) -> XpansionSettings:
        if constraint:
            settings = replace(settings, additional_constraints=None)
        if weight:
            settings = replace(settings, yearly_weights=None)
        return self._update_settings(settings, None)[0]

    @override
    def update_sensitivity(
        self,
        sensitivity: XpansionSensitivityUpdate,
        current_settings: XpansionSettings,
        current_sensitivity: XpansionSensitivity,
    ) -> XpansionSensitivity:
        # We have to send `yearly-weights` and `additional-constraints` fields to the Web API otherwise it deletes them.
        # We also have to re-send the sensitivity as a whole
        new_sensitivity = update_xpansion_sensitivity(current_sensitivity, sensitivity)
        return self._update_settings(current_settings, new_sensitivity)[1]

    def _update_settings(
        self, settings: XpansionSettings, sensitivity: XpansionSensitivity | None
    ) -> tuple[XpansionSettings, XpansionSensitivity]:
        try:
            body = serialize_xpansion_settings_api(settings, sensitivity)
            response = self._wrapper.put(f"{self._expansion_url}/settings", json=body).json()
            return parse_xpansion_settings_api(response)
        except APIError as e:
            raise XpansionSettingsEditionError(self._study_id, e.message) from e

    def _delete_matrix(self, file_name: str, url: str) -> None:
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise XpansionFileDeletionError(self._study_id, file_name, e.message) from e

    def _serialize_constraints(self, file_name: str, constraints: dict[str, XpansionConstraint]) -> None:
        url = f"{self._base_url}/studies/{self._study_id}/raw?path=user/expansion/constraints/{file_name}"
        api_content = serialize_xpansion_constraints_api(constraints)
        self._wrapper.put(url, files={"file": (file_name, api_content)})

    def _read_settings_and_sensitivity(self) -> tuple[XpansionSettings, XpansionSensitivity]:
        api_settings = self._wrapper.get(f"{self._expansion_url}/settings").json()
        return parse_xpansion_settings_api(api_settings)

    def _read_candidates(self) -> dict[str, XpansionCandidate]:
        candidates_api = self._wrapper.get(f"{self._expansion_url}/candidates").json()
        candidates = {}
        for cdt_api in candidates_api:
            cdt = parse_xpansion_candidate_api(cdt_api)
            candidates[cdt.name] = cdt
        return candidates

    def _read_constraints(self, file_name: str) -> dict[str, XpansionConstraint]:
        constraints_api = self._wrapper.get(f"{self._expansion_url}/resources/constraints/{file_name}").json()
        return parse_xpansion_constraints_api(constraints_api)
