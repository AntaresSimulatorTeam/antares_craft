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
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from typing_extensions import override

from antares.craft import ScenarioBuilder
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.api_conf.request_wrapper import RequestWrapper
from antares.craft.exceptions.exceptions import (
    APIError,
    BindingConstraintDeletionError,
    OutputDeletionError,
    OutputsRetrievalError,
    ScenarioBuilderEditionError,
    ScenarioBuilderReadingError,
    StudyDeletionError,
    StudyMoveError,
    StudyVariantCreationError,
    TaskFailedError,
    TaskTimeOutError,
    ThermalTimeseriesGenerationError,
)
from antares.craft.model.area import Area
from antares.craft.model.binding_constraint import (
    BindingConstraint,
)
from antares.craft.model.output import Output
from antares.craft.service.api_services.models.scenario_builder import ScenarioBuilderAPI
from antares.craft.service.api_services.utils import wait_task_completion
from antares.craft.service.base_services import BaseOutputService, BaseStudyService

if TYPE_CHECKING:
    from antares.craft.model.study import Study


class StudyApiService(BaseStudyService):
    def __init__(self, config: APIconf, study_id: str, output_service: BaseOutputService):
        super().__init__()
        self._config = config
        self._study_id = study_id
        self._base_url = f"{self.config.get_host()}/api/v1"
        self._wrapper = RequestWrapper(self.config.set_up_api_conf())
        self._output_service: BaseOutputService = output_service

    @property
    @override
    def study_id(self) -> str:
        return self._study_id

    @property
    @override
    def config(self) -> APIconf:
        return self._config

    @property
    def output_service(self) -> BaseOutputService:
        return self._output_service

    @override
    def delete_binding_constraint(self, constraint: BindingConstraint) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/bindingconstraints/{constraint.id}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise BindingConstraintDeletionError(constraint.id, e.message) from e

    @override
    def delete(self, children: bool) -> None:
        url = f"{self._base_url}/studies/{self.study_id}?children={children}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise StudyDeletionError(self.study_id, e.message) from e

    @override
    def create_variant(self, variant_name: str) -> "Study":
        from antares.craft.service.api_services.factory import read_study_api

        url = f"{self._base_url}/studies/{self.study_id}/variants?name={variant_name}"
        try:
            response = self._wrapper.post(url)
            variant_id = response.json()
            return read_study_api(self.config, variant_id)
        except APIError as e:
            raise StudyVariantCreationError(self.study_id, e.message) from e

    @override
    def read_outputs(self) -> dict[str, Output]:
        all_outputs: dict[str, Output] = {}
        url = f"{self._base_url}/studies/{self.study_id}/outputs"
        try:
            response = self._wrapper.get(url)
            outputs_json_list = response.json()
            for otp in outputs_json_list:
                output = Output(output_service=self.output_service, name=otp["name"], archived=otp["archived"])
                all_outputs[output.name] = output
            return all_outputs
        except APIError as e:
            raise OutputsRetrievalError(self.study_id, e.message)

    @override
    def delete_outputs(self) -> None:
        outputs_url = f"{self._base_url}/studies/{self.study_id}/outputs"
        try:
            response = self._wrapper.get(outputs_url)
            outputs_json_list = response.json()
            if not outputs_json_list:
                raise OutputsRetrievalError(self.study_id, "No outputs to delete.")
            for output in outputs_json_list:
                output_name = output["name"]
                self.delete_output(output_name)
        except APIError as e:
            raise OutputsRetrievalError(self.study_id, e.message)

    @override
    def delete_output(self, output_name: str) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/outputs/{output_name}"
        try:
            self._wrapper.delete(url)
        except APIError as e:
            raise OutputDeletionError(self.study_id, output_name, e.message) from e

    @override
    def move_study(self, new_parent_path: Path) -> PurePath:
        url = f"{self._base_url}/studies/{self.study_id}/move?folder_dest={new_parent_path}"
        try:
            self._wrapper.put(url)
            json_study = self._wrapper.get(f"{self._base_url}/studies/{self.study_id}").json()
            folder = json_study.pop("folder")
            return PurePath(folder) if folder else PurePath(".")
        except APIError as e:
            raise StudyMoveError(self.study_id, new_parent_path.as_posix(), e.message) from e

    @override
    def generate_thermal_timeseries(self, nb_years: int, areas: dict[str, Area], seed: int) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/timeseries/generate"
        url_config = f"{self._base_url}/studies/{self.study_id}/timeseries/config"
        json_thermal_timeseries = {"thermal": {"number": nb_years}}
        try:
            self._wrapper.put(url_config, json=json_thermal_timeseries)
            response = self._wrapper.put(url)
            task_id = response.json()
            wait_task_completion(self._base_url, self._wrapper, task_id)
        except (APIError, TaskFailedError, TaskTimeOutError) as e:
            raise ThermalTimeseriesGenerationError(self.study_id, e.message)

    @override
    def get_scenario_builder(self, nb_years: int) -> ScenarioBuilder:
        url = f"{self._base_url}/studies/{self.study_id}/config/scenariobuilder"
        try:
            json_response = self._wrapper.get(url).json()
            api_model = ScenarioBuilderAPI.from_api(json_response)
            return api_model.to_user_model(nb_years)
        except APIError as e:
            raise ScenarioBuilderReadingError(self.study_id, e.message)

    @override
    def set_scenario_builder(self, scenario_builder: ScenarioBuilder) -> None:
        url = f"{self._base_url}/studies/{self.study_id}/config/scenariobuilder"
        try:
            api_model = ScenarioBuilderAPI.from_user_model(scenario_builder)
            body = api_model.to_api()
            self._wrapper.put(url, json=body)
        except APIError as e:
            raise ScenarioBuilderEditionError(self.study_id, e.message)
