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

from typing import List


class InvalidChoiceError(ValueError):
    def __init__(self, message: str = "Invalid choice") -> None:
        self.message = message
        super().__init__(self.message)


class APIError(Exception):
    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(self.message)


class MissingTokenError(Exception):
    def __init__(self) -> None:
        super().__init__("Action can't be completed, you need to provide an api_token")


class AreaCreationError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not create the area {area_name}: " + message
        super().__init__(self.message)


class AreaPropertiesUpdateError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not update properties for area {area_name}: " + message
        super().__init__(self.message)


class AreaUiUpdateError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not update ui for area {area_name}: " + message
        super().__init__(self.message)


class AreaDeletionError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not delete the area {area_name}: " + message
        super().__init__(self.message)


class LinkCreationError(Exception):
    def __init__(self, area_from: str, area_to: str, message: str) -> None:
        self.message = f"Could not create the link {area_from} / {area_to}: " + message
        super().__init__(self.message)


class LinkPropertiesUpdateError(Exception):
    def __init__(self, link_name: str, message: str) -> None:
        self.message = f"Could not update properties for link {link_name}: " + message
        super().__init__(self.message)


class LinkUiUpdateError(Exception):
    def __init__(self, link_name: str, message: str) -> None:
        self.message = f"Could not update ui for link {link_name}: " + message
        super().__init__(self.message)


class LinkDeletionError(Exception):
    def __init__(self, link_name: str, message: str) -> None:
        self.message = f"Could not delete the link {link_name}: " + message
        super().__init__(self.message)


class ThermalCreationError(Exception):
    def __init__(self, thermal_name: str, area_id: str, message: str) -> None:
        self.message = f"Could not create the thermal cluster {thermal_name} inside area {area_id}: " + message
        super().__init__(self.message)


class ThermalPropertiesUpdateError(Exception):
    def __init__(self, thermal_name: str, area_id: str, message: str) -> None:
        self.message = (
            f"Could not update properties for thermal cluster {thermal_name} inside area {area_id}: " + message
        )
        super().__init__(self.message)


class ThermalDeletionError(Exception):
    def __init__(self, area_id: str, thermal_names: List[str], message: str) -> None:
        self.message = (
            f"Could not delete the following thermal clusters: {', '.join(thermal_names)} inside area {area_id}: "
            + message
        )
        super().__init__(self.message)


class HydroCreationError(Exception):
    def __init__(self, area_id: str, message: str) -> None:
        self.message = f"Could not create hydro inside area {area_id}: " + message
        super().__init__(self.message)


class RenewableCreationError(Exception):
    def __init__(self, renewable_name: str, area_id: str, message: str) -> None:
        self.message = f"Could not create the renewable cluster {renewable_name} inside area {area_id}: " + message
        super().__init__(self.message)


class RenewablePropertiesUpdateError(Exception):
    def __init__(self, renewable_name: str, area_id: str, message: str) -> None:
        self.message = (
            f"Could not update properties for renewable cluster {renewable_name} inside area {area_id}: " + message
        )
        super().__init__(self.message)


class RenewableDeletionError(Exception):
    def __init__(self, area_id: str, renewable_names: List[str], message: str) -> None:
        self.message = (
            f"Could not delete the following renewable clusters: {', '.join(renewable_names)} inside area {area_id}: "
            + message
        )
        super().__init__(self.message)


class STStorageCreationError(Exception):
    def __init__(self, st_storage_name: str, area_id: str, message: str) -> None:
        self.message = f"Could not create the short term storage {st_storage_name} inside area {area_id}: " + message
        super().__init__(self.message)


class STStoragePropertiesUpdateError(Exception):
    def __init__(self, st_storage_name: str, area_id: str, message: str) -> None:
        self.message = (
            f"Could not update properties for short term storage {st_storage_name} inside area {area_id}: " + message
        )
        super().__init__(self.message)


class STStorageMatrixDownloadError(Exception):
    def __init__(self, area_name: str, storage_name: str, matrix_name: str, message: str) -> None:
        self.message = (
            f"Could not download {matrix_name} matrix for storage {storage_name} inside area {area_name}: " + message
        )
        super().__init__(self.message)


class STStorageMatrixUploadError(Exception):
    def __init__(self, area_name: str, storage_name: str, matrix_name: str, message: str) -> None:
        self.message = (
            f"Could not upload {matrix_name} matrix for storage {storage_name} inside area {area_name}: " + message
        )
        super().__init__(self.message)


class STStorageDeletionError(Exception):
    def __init__(self, area_id: str, st_storage_names: List[str], message: str) -> None:
        self.message = (
            f"Could not delete the following short term storages: {', '.join(st_storage_names)} inside area {area_id}: "
            + message
        )
        super().__init__(self.message)


class BindingConstraintCreationError(Exception):
    def __init__(self, constraint_name: str, message: str) -> None:
        self.message = f"Could not create the binding constraint {constraint_name}: " + message
        super().__init__(self.message)


class ConstraintPropertiesUpdateError(Exception):
    def __init__(self, constraint_name: str, message: str) -> None:
        self.message = f"Could not update properties for binding constraint {constraint_name}: " + message
        super().__init__(self.message)


class ConstraintMatrixUpdateError(Exception):
    def __init__(self, constraint_name: str, matrix_name: str, message: str) -> None:
        self.message = f"Could not update matrix {matrix_name} for binding constraint {constraint_name}: " + message
        super().__init__(self.message)


class ConstraintMatrixDownloadError(Exception):
    def __init__(self, constraint_name: str, matrix_name: str, message: str) -> None:
        self.message = f"Could not download matrix {matrix_name} for binding constraint {constraint_name}: " + message
        super().__init__(self.message)


class ConstraintTermAdditionError(Exception):
    def __init__(self, constraint_name: str, terms_ids: List[str], message: str) -> None:
        self.message = (
            f"Could not add the following constraint terms: {', '.join(terms_ids)} inside constraint {constraint_name}: "
            + message
        )
        super().__init__(self.message)


class BindingConstraintDeletionError(Exception):
    def __init__(self, constraint_name: str, message: str) -> None:
        self.message = f"Could not delete the binding constraint {constraint_name}: " + message
        super().__init__(self.message)


class ConstraintTermDeletionError(Exception):
    def __init__(self, constraint_id: str, term_id: str, message: str) -> None:
        self.message = f"Could not delete the term {term_id} of the binding constraint {constraint_id}: " + message
        super().__init__(self.message)


class StudyCreationError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not create the study {study_name}: " + message
        super().__init__(self.message)


class StudySettingsUpdateError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not update settings for study {study_name}: " + message
        super().__init__(self.message)


class StudyDeletionError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not delete the study {study_id}: " + message
        super().__init__(self.message)


class LoadMatrixUploadError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not upload load matrix for area {area_name}: " + message
        super().__init__(self.message)


class LoadMatrixDownloadError(Exception):
    def __init__(self, area_name: str, message: str) -> None:
        self.message = f"Could not download load matrix for area {area_name}: " + message
        super().__init__(self.message)


class ThermalMatrixDownloadError(Exception):
    def __init__(self, area_name: str, cluster_name: str, matrix_name: str, message: str) -> None:
        self.message = (
            f"Could not download {matrix_name} for cluster {cluster_name} inside area {area_name}: " + message
        )
        super().__init__(self.message)


class RenewableMatrixDownloadError(Exception):
    def __init__(self, area_name: str, renewable_name: str, message: str) -> None:
        self.message = f"Could not download matrix for cluster {renewable_name} inside area {area_name}: " + message
        super().__init__(self.message)


class MatrixUploadError(Exception):
    def __init__(self, area_id: str, message: str) -> None:
        self.message = f"Error uploading matrix for area {area_id}: {message}"
        super().__init__(self.message)


class CustomError(Exception):
    def __init__(self, message: str = "Error") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigurationError(Exception):
    def __init__(self, message: str = "Error") -> None:
        self.message = "Unsupported configuration type" + f" {message}" if message != "Error" else ""
        super().__init__(self.message)
