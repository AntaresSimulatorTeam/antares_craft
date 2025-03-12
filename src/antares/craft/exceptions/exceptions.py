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

from typing import Any, List


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


class AreasRetrievalError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not retrieve the areas from the study {study_id} : " + message
        super().__init__(self.message)


class AreasUpdateError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not update the areas from the study {study_id} : {message}"
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


class LinksRetrievalError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not retrieve links from study {study_id} : {message}"
        super().__init__(self.message)


class LinksUpdateError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not update links from study {study_id} : {message}"
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


class ThermalsUpdateError(Exception):
    def __init__(self, study_id: str, message: str):
        self.message = f"Could not update the clusters from the study {study_id} : {message}"
        super().__init__(self.message)


class HydroCreationError(Exception):
    def __init__(self, area_id: str, message: str) -> None:
        self.message = f"Could not create hydro inside area {area_id}: " + message
        super().__init__(self.message)


class HydroPropertiesUpdateError(Exception):
    def __init__(self, area_id: str, message: str) -> None:
        self.message = f"Could not update hydro properties for area {area_id}: " + message
        super().__init__(self.message)


class HydroPropertiesReadingError(Exception):
    def __init__(self, area_id: str, message: str) -> None:
        self.message = f"Could not read hydro properties for area {area_id}: " + message
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


class BindingConstraintsUpdateError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not update binding constraints from the study {study_id}: {message}"
        super().__init__(self.message)


class ConstraintDoesNotExistError(Exception):
    def __init__(self, constraint_name: str, study_name: str) -> None:
        self.message = f"The binding constraint {constraint_name} doesn't exist inside study {study_name}."
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


class ConstraintTermEditionError(Exception):
    def __init__(self, constraint_id: str, term_id: str, message: str) -> None:
        self.message = f"Could not update the term {term_id} of the binding constraint {constraint_id}: " + message
        super().__init__(self.message)


class StudyCreationError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not create the study {study_name}: " + message
        super().__init__(self.message)


class StudySettingsUpdateError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not update settings for study {study_name}: " + message
        super().__init__(self.message)


class StudySettingsReadError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not read settings for study {study_name}: " + message
        super().__init__(self.message)


class StudyDeletionError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not delete the study {study_id}: " + message
        super().__init__(self.message)


class StudyVariantCreationError(Exception):
    def __init__(self, study_name: str, message: str) -> None:
        self.message = f"Could not create a variant for {study_name}: " + message
        super().__init__(self.message)


class StudyMoveError(Exception):
    def __init__(self, study_id: str, new_folder_name: str, message: str) -> None:
        self.message = f"Could not move the study {study_id} to folder {new_folder_name}: " + message
        super().__init__(self.message)


class StudyImportError(Exception):
    def __init__(self, study_id: str, message: str):
        self.message = f"Could not import the study {study_id} : {message}"
        super().__init__(self.message)


class ThermalMatrixDownloadError(Exception):
    def __init__(self, area_name: str, cluster_name: str, matrix_name: str, message: str) -> None:
        self.message = (
            f"Could not download {matrix_name} for cluster {cluster_name} inside area {area_name}: " + message
        )
        super().__init__(self.message)


class ThermalMatrixUpdateError(Exception):
    def __init__(self, area_name: str, cluster_name: str, matrix_name: str, message: str) -> None:
        self.message = f"Could not upload {matrix_name} for cluster {cluster_name} inside area {area_name}: " + message
        super().__init__(self.message)


class RenewableMatrixDownloadError(Exception):
    def __init__(self, area_name: str, renewable_name: str, message: str) -> None:
        self.message = f"Could not download matrix for cluster {renewable_name} inside area {area_name}: " + message
        super().__init__(self.message)


class RenewableMatrixUpdateError(Exception):
    def __init__(self, area_name: str, renewable_name: str, message: str) -> None:
        self.message = f"Could not upload matrix for cluster {renewable_name} inside area {area_name}: " + message
        super().__init__(self.message)


class MatrixUploadError(Exception):
    def __init__(self, area_id: str, matrix_type: str, message: str) -> None:
        self.message = f"Error uploading {matrix_type} matrix for area {area_id}: {message}"
        super().__init__(self.message)


class MatrixDownloadError(Exception):
    def __init__(self, area_id: str, matrix_type: str, message: str) -> None:
        self.message = f"Error downloading {matrix_type} matrix for area {area_id}: {message}"
        super().__init__(self.message)


class LinkUploadError(Exception):
    def __init__(self, area_from_id: str, area_to_id: str, matrix_type: str, message: str) -> None:
        self.message = f"Error uploading {matrix_type} matrix for link {area_from_id}/{area_to_id}: {message}"
        super().__init__(self.message)


class LinkDownloadError(Exception):
    def __init__(self, area_from_id: str, area_to_id: str, matrix_type: str, message: str):
        self.message = f"Could not download {matrix_type} matrix for link {area_from_id}/{area_to_id}: {message}"
        super().__init__(self.message)


class CustomError(Exception):
    def __init__(self, message: str = "Error") -> None:
        self.message = message
        super().__init__(self.message)


class ConfigurationError(Exception):
    def __init__(self, message: str = "Error") -> None:
        self.message = "Unsupported configuration type" + f" {message}" if message != "Error" else ""
        super().__init__(self.message)


class AntaresSimulationRunningError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not run the simulation for study {study_id}: " + message
        super().__init__(self.message)


class SimulationTimeOutError(Exception):
    def __init__(self, job_id: str, time_out: int) -> None:
        self.message = f"Job {job_id} exceeded timeout of {time_out} seconds"
        super().__init__(self.message)


class TaskTimeOutError(Exception):
    def __init__(self, task_id: str, time_out: int) -> None:
        self.message = f"Task {task_id} exceeded timeout of {time_out} seconds"
        super().__init__(self.message)


class TaskFailedError(Exception):
    def __init__(self, task_id: str) -> None:
        self.message = f"Task {task_id} failed"
        super().__init__(self.message)


class AntaresSimulationUnzipError(Exception):
    def __init__(self, study_id: str, job_id: str, message: str) -> None:
        self.message = f"Could not unzip simulation for study {study_id} and job {job_id}: " + message
        super().__init__(self.message)


class SimulationFailedError(Exception):
    def __init__(self, study_id: str, job_id: str) -> None:
        self.message = f"Simulation failed for {study_id} and job {job_id}"
        super().__init__(self.message)


class OutputsRetrievalError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not get outputs for {study_id}: " + message
        super().__init__(self.message)


class OutputDeletionError(Exception):
    def __init__(self, study_id: str, output_name: str, message: str) -> None:
        self.message = f"Could not delete the output {output_name} from study {study_id}: " + message
        super().__init__(self.message)


class ConstraintRetrievalError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not get binding constraints for {study_id}: " + message
        super().__init__(self.message)


class AggregateCreationError(Exception):
    def __init__(self, study_id: str, output_id: str, mc_type: str, object_type: str, message: str) -> None:
        self.message = (
            f"Could not create {mc_type}/{object_type} aggregate for study {study_id}, output {output_id}: " + message
        )
        super().__init__(self.message)


class ThermalTimeseriesGenerationError(Exception):
    def __init__(self, study_id: str, message: str) -> None:
        self.message = f"Could not generate thermal timeseries for study {study_id}: " + message
        super().__init__(self.message)


class FilteringValueError(Exception):
    def __init__(self, invalid_options: list[str], valid_values: set[str]) -> None:
        self.message = (
            f"Invalid value(s) in filters: {', '.join(invalid_options)}. Allowed values are: {', '.join(valid_values)}."
        )
        super().__init__(self.message)


class MatrixFormatError(Exception):
    def __init__(self, matrix_name: str, expected_shape: tuple[int, Any], actual_shape: tuple[int, int]) -> None:
        self.message = f"Wrong format for {matrix_name} matrix, expected shape is ({expected_shape[0]}, {expected_shape[1]}) and was : {actual_shape}"
        super().__init__(self.message)
