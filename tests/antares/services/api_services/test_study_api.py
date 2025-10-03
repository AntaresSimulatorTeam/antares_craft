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

import pytest
import requests_mock

import re

from io import StringIO
from json import dumps
from pathlib import Path, PurePath
from unittest.mock import Mock, patch

import pandas as pd

from antares.craft import (
    AdequacyPatchParametersUpdate,
    create_study_api,
    create_variant_api,
    import_study_api,
    read_study_api,
)
from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    AreaCreationError,
    AreasPropertiesUpdateError,
    BindingConstraintCreationError,
    ConstraintRetrievalError,
    ConstraintsPropertiesUpdateError,
    LinkCreationError,
    LinksPropertiesUpdateError,
    OutputDeletionError,
    OutputsRetrievalError,
    ScenarioBuilderReadingError,
    SimulationFailedError,
    SimulationTimeOutError,
    StudyCreationError,
    StudyImportError,
    StudyMoveError,
    StudySettingsUpdateError,
    StudyVariantCreationError,
    ThermalTimeseriesGenerationError,
)
from antares.craft.model.area import Area, AreaPropertiesUpdate, AreaUi
from antares.craft.model.binding_constraint import (
    BindingConstraint,
    BindingConstraintFrequency,
    BindingConstraintOperator,
    BindingConstraintProperties,
    BindingConstraintPropertiesUpdate,
    LinkData,
)
from antares.craft.model.commons import FilterOption
from antares.craft.model.link import Link, LinkProperties, LinkPropertiesUpdate
from antares.craft.model.output import (
    Frequency,
    MCAllAreasDataType,
    MCAllLinksDataType,
    MCIndAreasDataType,
    MCIndLinksDataType,
    Output,
)
from antares.craft.model.settings.general import GeneralParameters, GeneralParametersUpdate, Mode
from antares.craft.model.settings.study_settings import StudySettingsUpdate
from antares.craft.model.simulation import AntaresSimulationParameters, Job, JobStatus, Solver
from antares.craft.model.study import Study
from antares.craft.service.api_services.factory import create_api_services
from antares.craft.service.api_services.models.area import AreaPropertiesAPI, AreaUiAPI
from antares.craft.service.api_services.models.binding_constraint import BindingConstraintPropertiesAPI
from antares.craft.service.api_services.models.hydro import HydroPropertiesAPI
from antares.craft.service.api_services.models.link import LinkPropertiesAndUiAPI
from antares.craft.service.api_services.services.output import OutputApiService
from antares.craft.service.utils import read_output_matrix


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    antares_web_description_msg = "Mocked Server KO"
    services = create_api_services(api, study_id)
    study = Study("TestStudy", "880", services)
    area = Area(
        "area_test",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    area_1 = Area(
        "area_test_1",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )
    area_2 = Area(
        "area_test_2",
        services.area_service,
        services.short_term_storage_service,
        services.thermal_service,
        services.renewable_service,
        services.hydro_service,
    )

    first_link = Link(area.id, area_1.id, services.link_service)
    second_link = Link(area.id, area_2.id, services.link_service)

    b_constraint_1 = BindingConstraint("battery_state_evolution", services.bc_service)
    b_constraint_2 = BindingConstraint("battery_state_update", services.bc_service)

    output_link = Output(name="test-output-link", output_service=OutputApiService(api, study_id), archived=False)

    output_area = Output(name="test-output-area", output_service=OutputApiService(api, study_id), archived=False)

    def test_create_study_test_ok(self) -> None:
        with requests_mock.Mocker() as mocker:
            expected_url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            mocker.post(expected_url, json=self.study_id, status_code=200)
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.get(config_urls, json={}, status_code=200)
            ts_settings_url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"
            mocker.get(ts_settings_url, json={"thermal": {"number": 1}}, status_code=200)
            expected_url_path = f"https://antares.com/api/v1/studies/{self.study_id}"
            mocker.get(
                expected_url_path,
                json={
                    "id": f"{self.study_id}",
                    "name": f"{self.study.name}",
                    "version": f"{self.study._version}",
                    "folder": None,
                },
                status_code=200,
            )
            # When
            study = create_study_api("TestStudy", "880", self.api)

            # Then
            assert len(mocker.request_history) == 8
            assert mocker.request_history[0].url == expected_url
            assert isinstance(study, Study)

    def test_create_study_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            study_name = "TestStudy"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                StudyCreationError,
                match=f"Could not create the study '{study_name}': {self.antares_web_description_msg}",
            ):
                create_study_api(study_name, "880", self.api)

    def test_update_study_settings_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            settings = StudySettingsUpdate()
            settings.general_parameters = GeneralParametersUpdate(mode=Mode.ADEQUACY)
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.put(config_urls, status_code=200, json={})
            ts_settings_url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"
            mocker.get(ts_settings_url, json={"thermal": {"number": 1}}, status_code=200)
            self.study.update_settings(settings)

    def test_update_study_settings_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            settings = StudySettingsUpdate()
            settings.adequacy_patch_parameters = AdequacyPatchParametersUpdate(include_adq_patch=True)
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            antares_web_description_msg = "Server KO"
            mocker.put(config_urls, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                StudySettingsUpdateError,
                match=f"Could not update settings for study '{self.study_id}': {antares_web_description_msg}",
            ):
                self.study.update_settings(settings)

    def test_create_area_success(self) -> None:
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"

            ui = AreaUi(x=12, y=4, color_rgb=[16, 23, 3])
            url1 = f"{base_url}/studies/{self.study_id}/areas"
            mocker.post(url1, json={"id": area_name}, status_code=201)
            area_ui = AreaUiAPI.from_user_model(ui).model_dump()
            mocker.get(url1, json={area_name: area_ui}, status_code=201)
            url2 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/properties/form"
            url3 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/hydro/form"
            url4 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/hydro/inflow-structure"
            mocker.put(url2, status_code=201)
            mocker.get(url2, json=AreaPropertiesAPI(**{}).model_dump(), status_code=200)
            mocker.get(url3, json=HydroPropertiesAPI(**{}).model_dump())
            mocker.get(url4, json={"interMonthlyCorrelation": 0.5})
            area = self.study.create_area(area_name)
        assert isinstance(area, Area)

    def test_create_area_fails(self) -> None:
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                AreaCreationError,
                match=f"Could not create the area '{area_name}': {self.antares_web_description_msg}",
            ):
                self.study.create_area(area_name)

    def test_create_link_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/links"
            json_response = LinkPropertiesAndUiAPI(**{}).model_dump(by_alias=True)
            mocker.post(url, status_code=200, json={"area1": "", "area2": "", **json_response})
            self.study._areas["area"] = Area(
                "area",
                self.study._area_service,
                Mock(),
                Mock(),
                Mock(),
                Mock(),
            )
            self.study._areas["area_to"] = Area(
                "area_to",
                self.study._area_service,
                Mock(),
                Mock(),
                Mock(),
                Mock(),
            )

            link = self.study.create_link(area_from="area", area_to="area_to")
            assert isinstance(link, Link)

    def test_create_binding_constraint_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            properties = BindingConstraintProperties(enabled=False, filter_synthesis={FilterOption.ANNUAL})
            json_response = BindingConstraintPropertiesAPI.from_user_model(properties).model_dump(
                mode="json", by_alias=True
            )
            constraint_name = "bc_1"
            mocker.post(url, json={"id": "id", "name": constraint_name, "terms": [], **json_response}, status_code=201)
            constraint = self.study.create_binding_constraint(name=constraint_name, properties=properties)
            assert constraint.name == constraint_name
            assert constraint.properties == properties

    def test_create_binding_constraint_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            constraint_name = "bc_1"

            with pytest.raises(
                BindingConstraintCreationError,
                match=f"Could not create the binding constraint '{constraint_name}': {self.antares_web_description_msg}",
            ):
                self.study.create_binding_constraint(name=constraint_name)

    def test_read_study_api(self) -> None:
        json_study = {
            "id": "22c52f44-4c2a-407b-862b-490887f93dd8",
            "name": "test_read_areas",
            "version": "880",
            "folder": None,
        }

        json_ui = {
            "zone": {
                "ui": {"x": 0, "y": 0, "color_r": 230, "color_g": 108, "color_b": 44, "layers": "0"},
                "layerX": {"0": 0},
                "layerY": {"0": 0},
                "layerColor": {"0": "230, 108, 44"},
            }
        }

        config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
        ts_settings_url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"

        base_url = "https://antares.com/api/v1"
        url = f"{base_url}/studies/{self.study_id}"
        area_url = f"{url}/areas"
        area_props_url = f"{url}/table-mode/areas"
        thermal_url = f"{url}/table-mode/thermals"
        renewable_url = f"{url}/table-mode/renewables"
        storage_url = f"{url}/table-mode/st-storages"
        storage_constraints_url = f"{url}/table-mode/st-storages-additional-constraints"
        output_url = f"{url}/outputs"
        constraints_url = f"{base_url}/studies/{self.study_id}/bindingconstraints"
        hydro_url = f"{url}/hydro"
        links_url = f"{url}/links"
        xpansion_url = f"{url}/extensions/xpansion/settings"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_study)
            mocker.get(config_urls, json={})
            mocker.get(ts_settings_url, json={"thermal": {"number": 1}}, status_code=200)
            mocker.get(area_url, json=json_ui)
            mocker.get(area_props_url, json={"zone": {}})
            mocker.get(renewable_url, json={})
            mocker.get(thermal_url, json={})
            mocker.get(storage_url, json={})
            mocker.get(storage_constraints_url, json={})
            mocker.get(
                output_url,
                json=[],
            )
            mocker.get(constraints_url, json=[])
            mocker.get(links_url, json=[])
            mocker.get(xpansion_url, status_code=404)
            mocker.get(
                hydro_url,
                json={
                    "zone": {
                        "managementOptions": {"reservoir_capacity": 4.5},
                        "inflowStructure": {"interMonthlyCorrelation": 0.9},
                    }
                },
            )
            actual_study = read_study_api(self.api, self.study_id)

            expected_study_name = json_study.pop("name")
            expected_study_version = json_study.pop("version")
            assert isinstance(expected_study_name, str)
            assert isinstance(expected_study_version, str)

            expected_study = Study(
                expected_study_name,
                expected_study_version,
                self.services,
                Path(),
            )

            assert actual_study.name == expected_study.name
            assert actual_study._version == expected_study._version
            assert actual_study.service.study_id == expected_study.service.study_id
            assert not actual_study.has_an_xpansion_configuration

    def test_create_variant_success(self) -> None:
        variant_name = "variant_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"
            url = f"{base_url}/studies/{self.study_id}/variants?name={variant_name}"
            variant_id = "variant_id"
            mocker.post(url, json=variant_id, status_code=201)

            variant_url = f"{base_url}/studies/{variant_id}"
            mocker.get(
                variant_url,
                json={"id": variant_id, "name": variant_name, "version": "880", "folder": None},
                status_code=200,
            )

            config_urls = re.compile(f"{variant_url}/config/.*")
            mocker.get(config_urls, json={}, status_code=200)
            ts_settings_url = f"https://antares.com/api/v1/studies/{variant_id}/timeseries/config"
            mocker.get(ts_settings_url, json={"thermal": {"number": 1}}, status_code=200)

            areas_url = f"{variant_url}/areas?ui=true"
            mocker.get(areas_url, json={}, status_code=200)

            thermal_url = f"{variant_url}/table-mode/thermals"
            renewable_url = f"{variant_url}/table-mode/renewables"
            storage_url = f"{variant_url}/table-mode/st-storages"
            storage_constraints_url = f"{variant_url}/table-mode/st-storages-additional-constraints"
            properties_url = f"{variant_url}/table-mode/areas"
            hydro_url = f"{variant_url}/hydro"
            xpansion_url = f"{variant_url}/extensions/xpansion/settings"
            mocker.get(renewable_url, json={})
            mocker.get(thermal_url, json={})
            mocker.get(storage_url, json={})
            mocker.get(storage_constraints_url, json={})
            mocker.get(properties_url, json={})
            mocker.get(hydro_url, json={})
            mocker.get(xpansion_url, status_code=404)

            output_url = f"{base_url}/studies/{variant_id}/outputs"
            mocker.get(
                output_url,
                json=[],
                status_code=200,
            )

            constraints_url = f"{base_url}/studies/{variant_id}/bindingconstraints"
            mocker.get(constraints_url, json=[], status_code=200)

            links_url = f"{base_url}/studies/{variant_id}/links"
            mocker.get(links_url, json=[], status_code=200)

            variant = self.study.create_variant(variant_name)
            variant_from_api = create_variant_api(self.api, self.study_id, variant_name)

            assert isinstance(variant, Study)
            assert isinstance(variant_from_api, Study)
            assert variant.name == variant_name
            assert variant_from_api.name == variant_name
            assert variant.service.study_id == variant_id
            assert variant_from_api.service.study_id == variant_id

    def test_create_variant_fails(self) -> None:
        variant_name = "variant_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"
            url = f"{base_url}/studies/{self.study_id}/variants?name={variant_name}"
            error_message = "Variant creation failed"
            mocker.post(url, json={"description": error_message}, status_code=404)

            with pytest.raises(StudyVariantCreationError, match=error_message):
                self.study.create_variant(variant_name)

            with pytest.raises(StudyVariantCreationError, match=error_message):
                create_variant_api(self.api, self.study_id, variant_name)

    def test_create_duplicated_link(self) -> None:
        area_a = "area_a"
        area_b = "area_b"

        self.study._areas[area_a] = Area(
            area_a,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )
        self.study._areas[area_b] = Area(
            area_b,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )

        existing_link = Link(area_a, area_b, Mock())
        self.study._links[existing_link.id] = existing_link

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link '{area_a} / {area_b}': A link from {area_a} to {area_b} already exists",
        ):
            self.study.create_link(area_from=area_b, area_to=area_a)

    def test_create_link_unknown_area(self) -> None:
        area_from = "area_fr"
        area_to = "area_missing"

        self.study._areas[area_from] = Area(
            area_from,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link '{area_from} / {area_to}': {area_to} does not exist",
        ):
            self.study.create_link(area_from=area_from, area_to=area_to)

    def test_create_link_same_area(self) -> None:
        area = "area_1"

        self.study._areas[area] = Area(
            area,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
            Mock(),
        )

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link '{area} / {area}': A link cannot start and end at the same area",
        ):
            self.study.create_link(area_from=area, area_to=area)

    def test_to_api_with_xpress_solver(self) -> None:
        simulation_parameters = AntaresSimulationParameters(solver=Solver.XPRESS, nb_cpu=34)

        payload = simulation_parameters.to_api()

        assert payload["auto_unzip"] is True
        assert payload["other_options"] == "xpress"
        assert payload["nb_cpu"] == 34

    def test_run_and_wait_antares_simulation(self) -> None:
        parameters = AntaresSimulationParameters(solver=Solver.COIN, nb_cpu=2, unzip_output=True, presolve=False)

        # patch simulates the repeating intervals so that we don't have to wait X seconds during the tests
        with requests_mock.Mocker() as mocker, patch("time.sleep", return_value=None):
            run_url = f"https://antares.com/api/v1/launcher/run/{self.study_id}"
            job_id = "1234-g6z17"
            mocker.post(run_url, json={"job_id": job_id}, status_code=200)

            job_url = f"https://antares.com/api/v1/launcher/jobs/{job_id}"
            output_id = "2024abcdefg-output"

            # ========== SUCCESS TEST ============

            parameters_as_api = dumps(parameters.to_api())
            # mock can take a list of responses that it maps one by one to each request, since we're doing multiple ones
            response_list = [
                {
                    "json": {
                        "id": job_id,
                        "status": "pending",
                        "launcher_params": parameters_as_api,
                    },
                    "status_code": 200,
                },
                {
                    "json": {
                        "id": job_id,
                        "status": "running",
                        "launcher_params": parameters_as_api,
                    },
                    "status_code": 200,
                },
                {
                    "json": {
                        "id": job_id,
                        "status": "success",
                        "launcher_params": parameters_as_api,
                        "output_id": output_id,
                    },
                    "status_code": 200,
                },
            ]
            mocker.get(job_url, response_list)

            tasks_url = "https://antares.com/api/v1/tasks"
            task_id = "task-5678"
            mocker.post(tasks_url, json=[{"id": task_id, "name": f"UNARCHIVE/{output_id}"}], status_code=200)

            task_url = f"{tasks_url}/{task_id}"
            mocker.get(task_url, json={"result": {"success": True}}, status_code=200)

            output_url = f"https://antares.com/api/v1/studies/{self.study_id}/outputs"
            mocker.get(output_url, json=[], status_code=200)

            job = self.study.run_antares_simulation(parameters)
            assert isinstance(job, Job)
            assert job.job_id == job_id
            assert job.status == JobStatus.PENDING

            self.study.wait_job_completion(job, time_out=10)

            assert job.status == JobStatus.SUCCESS  # type: ignore

            # ========= TIMEOUT TEST ==========

            response_list.pop()
            mocker.get(job_url, response_list)
            mocker.post(tasks_url, status_code=200)

            job = self.study.run_antares_simulation(parameters)
            with pytest.raises(SimulationTimeOutError):
                self.study.wait_job_completion(job, time_out=2)

            # =========== FAILED TEST ===========

            response_list.append(
                {
                    "json": {
                        "id": job_id,
                        "status": "failed",
                        "launcher_params": dumps(parameters.to_api()),
                    },
                    "status_code": 200,
                }
            )
            mocker.get(job_url, response_list)
            mocker.post(tasks_url, status_code=200)

            job = self.study.run_antares_simulation(parameters)
            with pytest.raises(SimulationFailedError):
                self.study.wait_job_completion(job, time_out=10)

    def test_read_outputs(self) -> None:
        with requests_mock.Mocker() as mocker:
            run_url = f"https://antares.com/api/v1/studies/{self.study_id}/outputs"

            json_output = [
                {
                    "name": "20241217-1115eco-sdqsd",
                    "type": "economy",
                    "settings": {},
                    "archived": False,
                },
                {
                    "name": "20241217-1115eco-abcd",
                    "type": "economy",
                    "settings": {},
                    "archived": True,
                },
            ]
            mocker.get(run_url, json=json_output, status_code=200)

            self.study._read_outputs()

            assert len(self.study.get_outputs()) == 2
            output1 = self.study.get_output(json_output[0]["name"])  # type: ignore
            output2 = self.study.get_output(json_output[1]["name"])  # type: ignore
            assert output1.archived == json_output[0].get("archived")
            assert output2.archived == json_output[1].get("archived")

            # ===== FAILING TEST =====
            error_message = f"Couldn't get outputs for study {self.study_id}"
            mocker.get(run_url, json={"description": error_message}, status_code=404)
            with pytest.raises(OutputsRetrievalError, match=error_message):
                self.study._read_outputs()

    def test_read_constraints_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            constraints_url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            json_constraints = [
                {
                    "id": "bc_1",
                    "name": "bc_1",
                    "enabled": True,
                    "time_step": "hourly",
                    "operator": "less",
                    "comments": "",
                    "filter_year_by_year": "hourly",
                    "filter_synthesis": "hourly",
                    "group": "default",
                    "terms": [
                        {
                            "data": {"area1": "area_a", "area2": "area_b"},
                            "weight": 1.0,
                            "offset": 0,
                            "id": "area_a%area_b",
                        }
                    ],
                }
            ]
            mocker.get(constraints_url, json=json_constraints, status_code=200)

            self.study._binding_constraints = {}
            self.study._read_binding_constraints()
            constraints = self.study.get_binding_constraints()

            assert len(constraints) == 1
            constraint = constraints["bc_1"]
            assert constraint.id == "bc_1"
            assert constraint.name == "bc_1"
            assert constraint.properties.enabled is True
            assert constraint.properties.time_step == BindingConstraintFrequency.HOURLY
            assert constraint.properties.operator == BindingConstraintOperator.LESS
            assert constraint.properties.group == "default"
            assert len(constraint.get_terms()) == 1
            term = constraint.get_terms()["area_a%area_b"]
            assert isinstance(term.data, LinkData)
            assert term.data.area1 == "area_a"
            assert term.data.area2 == "area_b"
            assert term.weight == 1.0
            assert term.offset == 0

    def test_read_constraints_fails(self) -> None:
        self.study._binding_constraints = {}
        with requests_mock.Mocker() as mocker:
            constraints_url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            error_message = "Error while reading constraints"
            mocker.get(constraints_url, json={"description": error_message}, status_code=404)
            with pytest.raises(ConstraintRetrievalError, match="Error while reading constraints"):
                self.study._read_binding_constraints()

    def test_output_get_mc_all(self, tmp_path: Path) -> None:
        self.study._areas["area_test"] = self.area
        self.study._areas["area_test_1"] = self.area_1
        self.study._outputs["test-output-link"] = self.output_link
        self.study._outputs["test-output-area"] = self.output_area

        frequency = Frequency.ANNUAL
        with requests_mock.Mocker() as mocker:
            matrix_link_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw/original-file?path=output/{self.output_link.name}/economy/mc-all/links/{self.area.id}/{self.area_1.id}/values-{frequency.value}"
            matrix_area_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw/original-file?path=output/{self.output_area.name}/economy/mc-all/areas/{self.area.id}/values-{frequency.value}"

            expected_area_content = """area_1	area	va	annual
	VARIABLES	BEGIN	END
	321	1	1

area_1	annual	OV. COST	OP. COST	OP. COST	OP. COST	OP. COST	MRG. PRICE	MRG. PRICE	MRG. PRICE	MRG. PRICE	CO2 EMIS.	CO2 EMIS.	CO2 EMIS.	CO2 EMIS.	NH3 EMIS.	NH3 EMIS.	NH3 EMIS.	NH3 EMIS.	SO2 EMIS.	SO2 EMIS.	SO2 EMIS.	SO2 EMIS.	NOX EMIS.	NOX EMIS.	NOX EMIS.	NOX EMIS.	PM2_5 EMIS.	PM2_5 EMIS.	PM2_5 EMIS.	PM2_5 EMIS.	PM5 EMIS.	PM5 EMIS.	PM5 EMIS.	PM5 EMIS.	PM10 EMIS.	PM10 EMIS.	PM10 EMIS.	PM10 EMIS.	NMVOC EMIS.	NMVOC EMIS.	NMVOC EMIS.	NMVOC EMIS.	OP1 EMIS.	OP1 EMIS.	OP1 EMIS.	OP1 EMIS.	OP2 EMIS.	OP2 EMIS.	OP2 EMIS.	OP2 EMIS.	OP3 EMIS.	OP3 EMIS.	OP3 EMIS.	OP3 EMIS.	OP4 EMIS.	OP4 EMIS.	OP4 EMIS.	OP4 EMIS.	OP5 EMIS.	OP5 EMIS.	OP5 EMIS.	OP5 EMIS.	BALANCE	BALANCE	BALANCE	BALANCE	ROW BAL.	PSP	MISC. NDG	LOAD	LOAD	LOAD	LOAD	H. ROR	H. ROR	H. ROR	H. ROR	NUCLEAR	NUCLEAR	NUCLEAR	NUCLEAR	LIGNITE	LIGNITE	LIGNITE	LIGNITE	COAL	COAL	COAL	COAL	GAS	GAS	GAS	GAS	OIL	OIL	OIL	OIL	MIX. FUEL	MIX. FUEL	MIX. FUEL	MIX. FUEL	MISC. DTG	MISC. DTG	MISC. DTG	MISC. DTG	MISC. DTG 2	MISC. DTG 2	MISC. DTG 2	MISC. DTG 2	MISC. DTG 3	MISC. DTG 3	MISC. DTG 3	MISC. DTG 3	MISC. DTG 4	MISC. DTG 4	MISC. DTG 4	MISC. DTG 4	WIND OFFSHORE	WIND OFFSHORE	WIND OFFSHORE	WIND OFFSHORE	WIND ONSHORE	WIND ONSHORE	WIND ONSHORE	WIND ONSHORE	SOLAR CONCRT.	SOLAR CONCRT.	SOLAR CONCRT.	SOLAR CONCRT.	SOLAR PV	SOLAR PV	SOLAR PV	SOLAR PV	SOLAR ROOFT	SOLAR ROOFT	SOLAR ROOFT	SOLAR ROOFT	RENW. 1	RENW. 1	RENW. 1	RENW. 1	RENW. 2	RENW. 2	RENW. 2	RENW. 2	RENW. 3	RENW. 3	RENW. 3	RENW. 3	RENW. 4	RENW. 4	RENW. 4	RENW. 4	H. STOR	H. STOR	H. STOR	H. STOR	H. PUMP	H. PUMP	H. PUMP	H. PUMP	H. LEV	H. LEV	H. LEV	H. LEV	H. INFL	H. INFL	H. INFL	H. INFL	H. OVFL	H. OVFL	H. OVFL	H. OVFL	H. VAL	H. VAL	H. VAL	H. VAL	H. COST	H. COST	H. COST	H. COST	PSP_open_injection	PSP_open_injection	PSP_open_injection	PSP_open_injection	PSP_open_withdrawal	PSP_open_withdrawal	PSP_open_withdrawal	PSP_open_withdrawal	PSP_open_level	PSP_open_level	PSP_open_level	PSP_open_level	PSP_closed_injection	PSP_closed_injection	PSP_closed_injection	PSP_closed_injection	PSP_closed_withdrawal	PSP_closed_withdrawal	PSP_closed_withdrawal	PSP_closed_withdrawal	PSP_closed_level	PSP_closed_level	PSP_closed_level	PSP_closed_level	Pondage_injection	Pondage_injection	Pondage_injection	Pondage_injection	Pondage_withdrawal	Pondage_withdrawal	Pondage_withdrawal	Pondage_withdrawal	Pondage_level	Pondage_level	Pondage_level	Pondage_level	Battery_injection	Battery_injection	Battery_injection	Battery_injection	Battery_withdrawal	Battery_withdrawal	Battery_withdrawal	Battery_withdrawal	Battery_level	Battery_level	Battery_level	Battery_level	Other1_injection	Other1_injection	Other1_injection	Other1_injection	Other1_withdrawal	Other1_withdrawal	Other1_withdrawal	Other1_withdrawal	Other1_level	Other1_level	Other1_level	Other1_level	Other2_injection	Other2_injection	Other2_injection	Other2_injection	Other2_withdrawal	Other2_withdrawal	Other2_withdrawal	Other2_withdrawal	Other2_level	Other2_level	Other2_level	Other2_level	Other3_injection	Other3_injection	Other3_injection	Other3_injection	Other3_withdrawal	Other3_withdrawal	Other3_withdrawal	Other3_withdrawal	Other3_level	Other3_level	Other3_level	Other3_level	Other4_injection	Other4_injection	Other4_injection	Other4_injection	Other4_withdrawal	Other4_withdrawal	Other4_withdrawal	Other4_withdrawal	Other4_level	Other4_level	Other4_level	Other4_level	Other5_injection	Other5_injection	Other5_injection	Other5_injection	Other5_withdrawal	Other5_withdrawal	Other5_withdrawal	Other5_withdrawal	Other5_level	Other5_level	Other5_level	Other5_level	UNSP. ENRG	UNSP. ENRG	UNSP. ENRG	UNSP. ENRG	SPIL. ENRG	SPIL. ENRG	SPIL. ENRG	SPIL. ENRG	LOLD	LOLD	LOLD	LOLD	LOLP	AVL DTG	AVL DTG	AVL DTG	AVL DTG	DTG MRG	DTG MRG	DTG MRG	DTG MRG	MAX MRG	MAX MRG	MAX MRG	MAX MRG	NP COST	NP COST	NP COST	NP COST	NODU	NODU	NODU	NODU
		Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	Tons	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	%	%	%	%	MWh	MWh	MWh	MWh	%	%	%	%	Euro/MWh	Euro/MWh	Euro/MWh	Euro/MWh	Euro	Euro	Euro	Euro	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MW	MW	MW	MW	MW	MW	MW	MW	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	Hours	Hours	Hours	Hours	%	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	Euro	Euro	Euro	Euro	 	 	 	 
		EXP	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	values	EXP	EXP	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	values	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max
	Annual	0	0	0	0	0	-0.0006	0	-0.0006	-0.0006	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	N/A	N/A	N/A	N/A	0	0	0	0	N/A	N/A	N/A	N/A	N/A	N/A	N/A	N/A	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0"""

            mocker.get(matrix_area_url, text=expected_area_content)
            matrix_area = self.output_area.get_mc_all_area(frequency, MCAllAreasDataType.VALUES, self.area.id)
            expected_matrix = read_output_matrix(StringIO(expected_area_content), frequency)
            assert matrix_area.equals(expected_matrix)

            expected_link_content = """area_1	link	va	annual
area_2	VARIABLES	BEGIN	END
	28	1	1

area_1	annual	FLOW LIN.	FLOW LIN.	FLOW LIN.	FLOW LIN.	UCAP LIN.	UCAP LIN.	UCAP LIN.	UCAP LIN.	LOOP FLOW	FLOW QUAD.	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	MARG. COST	MARG. COST	MARG. COST	MARG. COST	CONG. PROB +	CONG. PROB -	HURDLE COST	HURDLE COST	HURDLE COST	HURDLE COST
		MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro/MW	Euro/MW	Euro/MW	Euro/MW	%	%	Euro	Euro	Euro	Euro
		EXP	std	min	max	EXP	std	min	max	values	values	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	values	values	EXP	std	min	max
	Annual	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0"""

            mocker.get(matrix_link_url, text=expected_link_content)
            matrix_link = self.output_link.get_mc_all_link(
                frequency, MCAllLinksDataType.VALUES, self.area.id, self.area_1.id
            )
            expected_matrix = read_output_matrix(StringIO(expected_link_content), frequency)
            assert matrix_link.equals(expected_matrix)

    def test_output_get_mc_ind(self, tmp_path: Path) -> None:
        frequency = Frequency.ANNUAL
        with requests_mock.Mocker() as mocker:
            matrix_link_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw/original-file?path=output/{self.output_link.name}/economy/mc-ind/00001/links/{self.area.id}/{self.area_1.id}/values-{frequency.value}"
            matrix_area_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw/original-file?path=output/{self.output_area.name}/economy/mc-ind/00001/areas/{self.area.id}/values-{frequency.value}"

            expected_area_content = """area_1	link	va	annual
area_2	VARIABLES	BEGIN	END
	28	1	1

area_1	annual	FLOW LIN.	FLOW LIN.	FLOW LIN.	FLOW LIN.	UCAP LIN.	UCAP LIN.	UCAP LIN.	UCAP LIN.	LOOP FLOW	FLOW QUAD.	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ALG.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	CONG. FEE (ABS.)	MARG. COST	MARG. COST	MARG. COST	MARG. COST	CONG. PROB +	CONG. PROB -	HURDLE COST	HURDLE COST	HURDLE COST	HURDLE COST
		MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	MWh	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro	Euro/MW	Euro/MW	Euro/MW	Euro/MW	%	%	Euro	Euro	Euro	Euro
		EXP	std	min	max	EXP	std	min	max	values	values	EXP	std	min	max	EXP	std	min	max	EXP	std	min	max	values	values	EXP	std	min	max
	Annual	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0	0"""

            mocker.get(matrix_area_url, text=expected_area_content)
            matrix_area = self.output_area.get_mc_ind_area(1, frequency, MCIndAreasDataType.VALUES, self.area.id)
            expected_matrix = read_output_matrix(StringIO(expected_area_content), frequency)
            assert matrix_area.equals(expected_matrix)

            expected_link_content = """area_1	link	va	annual
area_2	VARIABLES	BEGIN	END
	10	1	1

area_1	annual	FLOW LIN.	UCAP LIN.	LOOP FLOW	FLOW QUAD.	CONG. FEE (ALG.)	CONG. FEE (ABS.)	MARG. COST	CONG. PROB +	CONG. PROB -	HURDLE COST
		MWh	MWh	MWh	MWh	Euro	Euro	Euro/MW	%	%	Euro
											
	Annual	0	0	0	0	0	0	0	0	0	0"""

            mocker.get(matrix_link_url, text=expected_link_content)
            matrix_link = self.output_link.get_mc_ind_link(
                1, frequency, MCIndLinksDataType.VALUES, self.area.id, self.area_1.id
            )
            expected_matrix_link = read_output_matrix(StringIO(expected_link_content), frequency)
            assert matrix_link.equals(expected_matrix_link)

    def test_output_aggregate_values(self) -> None:
        with requests_mock.Mocker() as mocker:
            output = Output(
                name="test-output", output_service=OutputApiService(self.api, self.study_id), archived=False
            )

            # aggregate_values_areas_mc_ind
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/outputs/{output.name}/aggregate/areas/mc-ind?query_file=values&frequency=annual&format=parquet"
            aggregate_output = ""
            download_id = "download-1"
            download_metadata_url = (
                f"https://antares.com/api/v1/downloads/{download_id}/metadata?wait_for_availability=True"
            )
            download_url = f"https://antares.com/api/v1/downloads/{download_id}"
            mocker.get(aggregate_url, json=download_id)
            mocker.get(download_metadata_url, json={})
            mocker.get(download_url, text=aggregate_output)
            aggregated_matrix = output.aggregate_mc_ind_areas(MCIndAreasDataType.VALUES, Frequency.ANNUAL)
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_links_mc_ind
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/links/aggregate/mc-ind/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, json=download_id)
            aggregated_matrix = output.aggregate_mc_ind_links(
                MCIndLinksDataType.VALUES, Frequency.ANNUAL, columns_names=["fr"]
            )
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_areas_mc_all
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/aggregate/mc-all/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, json=download_id)
            aggregated_matrix = output.aggregate_mc_all_areas(MCAllAreasDataType.VALUES, Frequency.ANNUAL)
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_links_mc_all
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/links/aggregate/mc-all/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, json=download_id)
            aggregated_matrix = output.aggregate_mc_all_links(MCAllLinksDataType.VALUES, Frequency.ANNUAL)
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

    def test_delete_output(self) -> None:
        output_name = "test_output"
        with requests_mock.Mocker() as mocker:
            outputs_url = f"https://antares.com/api/v1/studies/{self.study_id}/outputs"
            delete_url = f"{outputs_url}/{output_name}"
            mocker.get(outputs_url, json=[{"name": output_name, "archived": False}], status_code=200)
            mocker.delete(delete_url, status_code=200)

            self.study._read_outputs()
            assert output_name in self.study.get_outputs()
            self.study.delete_output(output_name)
            assert output_name not in self.study.get_outputs()

            # failing
            error_message = f"Output {output_name} deletion failed"
            mocker.delete(delete_url, json={"description": error_message}, status_code=404)

            with pytest.raises(OutputDeletionError, match=error_message):
                self.study.delete_output(output_name)

    def test_delete_outputs(self) -> None:
        with requests_mock.Mocker() as mocker:
            outputs_url = f"https://antares.com/api/v1/studies/{self.study_id}/outputs"
            outputs_json = [
                {"name": "output1", "archived": False},
                {"name": "output2", "archived": True},
            ]
            mocker.get(outputs_url, json=outputs_json, status_code=200)

            delete_url1 = f"https://antares.com/api/v1/studies/{self.study_id}/outputs/output1"
            delete_url2 = f"https://antares.com/api/v1/studies/{self.study_id}/outputs/output2"
            mocker.delete(delete_url1, status_code=200)
            mocker.delete(delete_url2, status_code=200)

            mocker.get(
                outputs_url,
                json=[{"name": "output1", "archived": False}, {"name": "output2", "archived": True}],
                status_code=200,
            )
            self.study._read_outputs()
            assert len(self.study.get_outputs()) == 2

            self.study.delete_outputs()
            assert len(self.study.get_outputs()) == 0

            # failing (nothing to delete)
            error_message = "Outputs deletion failed"
            mocker.get(outputs_url, json={"description": error_message}, status_code=404)
            with pytest.raises(OutputsRetrievalError, match=error_message):
                self.study.delete_outputs()

    def test_move_study(self) -> None:
        new_path = Path("/new/path/test")
        with requests_mock.Mocker() as mocker:
            move_url = f"https://antares.com/api/v1/studies/{self.study_id}/move?folder_dest={new_path}"
            study_url = f"https://antares.com/api/v1/studies/{self.study_id}"
            mocker.put(move_url, status_code=200)
            mocker.get(study_url, json={"folder": f"/new/path/test/{self.study_id}"}, status_code=200)

            assert self.study.path == PurePath(".")
            self.study.move(new_path)
            assert self.study.path == PurePath(new_path) / f"{self.study_id}"

            # Failing
            error_message = "Study move failed"
            mocker.put(move_url, json={"description": error_message}, status_code=404)
            with pytest.raises(StudyMoveError, match=error_message):
                self.study.move(new_path)

    def test_generate_thermal_timeseries_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/generate"
            url_config = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"
            task_id = "task-5678"
            mocker.put(url_config, json={})
            mocker.put(url, json=task_id, status_code=200)

            task_url = f"https://antares.com/api/v1/tasks/{task_id}"
            mocker.get(task_url, json={"result": {"success": True}}, status_code=200)

            with patch("antares.craft.service.api_services.utils.wait_task_completion", return_value=None):
                self.study.generate_thermal_timeseries(1)

    def test_generate_thermal_timeseries_failure(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/generate"
            url_config = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"
            error_message = f"Thermal timeseries generation failed for study {self.study_id}"
            mocker.put(url_config, json={"description": error_message}, status_code=404)
            mocker.put(url, json={"description": error_message}, status_code=404)

            with pytest.raises(ThermalTimeseriesGenerationError, match=error_message):
                self.study.generate_thermal_timeseries(1)

    def test_import_study_success(self, tmp_path: Path) -> None:
        json_study = {
            "id": "22c52f44-4c2a-407b-862b-490887f93dd8",
            "name": "test_read_areas",
            "version": "880",
            "folder": None,
        }

        study_path = tmp_path.joinpath("test.zip")
        study_path.touch()
        new_path = Path("/new/path/test")
        base_url = "https://antares.com/api/v1"

        url = f"{base_url}/studies/{self.study_id}"
        area_url = f"{url}/areas"
        area_props_url = f"{area_url}/zone/properties/form"
        thermal_url = f"{url}/table-mode/thermals"
        renewable_url = f"{url}/table-mode/renewables"
        storage_url = f"{url}/table-mode/st-storages"
        storage_constraints_url = f"{url}/table-mode/st-storages-additional-constraints"
        properties_url = f"{url}/table-mode/areas"
        output_url = f"{url}/outputs"
        constraints_url = f"{base_url}/studies/{self.study_id}/bindingconstraints"
        links_url = f"{base_url}/studies/{self.study_id}/links"
        config_urls = re.compile(f"{base_url}/studies/{self.study_id}/config/.*")
        ts_settings_url = f"https://antares.com/api/v1/studies/{self.study_id}/timeseries/config"
        hydro_url = f"{base_url}/studies/{self.study_id}/hydro"

        url_import = f"{base_url}/studies/_import"
        url_move = f"{base_url}/studies/{self.study_id}/move?folder_dest={new_path}"
        url_study = f"{base_url}/studies/{self.study_id}"
        url_xpansion = f"{base_url}/studies/{self.study_id}/extensions/xpansion/settings"

        with requests_mock.Mocker() as mocker:
            mocker.post(url_import, status_code=200, json=self.study_id)

            mocker.get(url, json=json_study)
            mocker.get(config_urls, json={})
            mocker.get(ts_settings_url, json={"thermal": {"number": 1}}, status_code=200)
            mocker.get(area_url, json={})
            mocker.get(area_props_url, json={})
            mocker.get(renewable_url, json={})
            mocker.get(thermal_url, json={})
            mocker.get(storage_url, json={})
            mocker.get(storage_constraints_url, json={})
            mocker.get(properties_url, json={})
            mocker.get(output_url, json=[])
            mocker.get(constraints_url, json=[])
            mocker.get(links_url, json=[])
            mocker.get(hydro_url, json={})
            mocker.get(url_xpansion, status_code=404)

            mocker.put(url_move)
            mocker.get(url_study, json=json_study)

            actual_study = import_study_api(self.api, study_path, new_path)

            assert actual_study.name == json_study["name"]
            assert actual_study.service.study_id == json_study["id"]

    def test_import_study_fail_wrong_extension(self) -> None:
        with pytest.raises(Exception, match=re.escape("File doesn't have the right extensions (.zip/.7z): .rar")):
            import_study_api(self.api, Path("test.rar"))

    def test_import_study_fail_api_error(self, tmp_path: Path) -> None:
        study_path = tmp_path.joinpath("test.zip")
        study_path.touch()

        base_url = "https://antares.com/api/v1"
        url_import = f"{base_url}/studies/_import"
        url_read_study = f"{base_url}/studies/{self.study_id}"

        with requests_mock.Mocker() as mocker:
            mocker.post(url_import, json=self.study_id)
            mocker.get(url_read_study, json={"description": self.antares_web_description_msg}, status_code=404)
            with pytest.raises(
                StudyImportError, match=f"Could not import the study 'test.zip' : {self.antares_web_description_msg}"
            ):
                import_study_api(self.api, study_path)

    def test_update_multiple_areas_success(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/areas"
        self.study._areas["area_test_1"] = self.area_1
        self.study._areas["area_test_2"] = self.area_2
        dict_areas = {}

        json_areas = [
            {
                self.area_1: {
                    "adequacy_patch_mode": "outside",
                    "non_dispatch_power": True,
                    "dispatch_hydro_power": True,
                    "other_dispatch_power": True,
                    "energy_cost_unsupplied": 0,
                    "energy_cost_spilled": 0,
                    "filter_synthesis": "annual",
                    "filter_by_year": "hourly, daily, annual",
                    "spread_unsupplied_energy_cost": 3000,
                    "spread_spilled_energy_cost": 0,
                },
                self.area_2: {
                    "adequacy_patch_mode": "outside",
                    "non_dispatch_power": True,
                    "dispatch_hydro_power": True,
                    "other_dispatch_power": True,
                    "energy_cost_unsupplied": 0,
                    "energy_cost_spilled": 0,
                    "filter_synthesis": "hourly, daily, weekly",
                    "filter_by_year": "weekly, monthly, annual",
                    "spread_unsupplied_energy_cost": 1400,
                    "spread_spilled_energy_cost": 0,
                },
            }
        ]

        json_areas_1 = [
            {
                "area_test_1": {
                    "adequacyPatchMode": "outside",
                    "nonDispatchPower": True,
                    "dispatchHydroPower": True,
                    "otherDispatchPower": True,
                    "energyCostUnsupplied": 0,
                    "energyCostSpilled": 0,
                    "filterSynthesis": "annual",
                    "filterYear": "hourly, daily, annual",
                    "spreadUnsuppliedEnergyCost": 3000,
                    "spreadSpilledEnergyCost": 0,
                },
                "area_test_2": {
                    "adequacyPatchMode": "outside",
                    "nonDispatchablePower": True,
                    "dispatchHydroPower": True,
                    "otherDispatchPower": True,
                    "energyCostUnsupplied": 0,
                    "energyCostSpilled": 0,
                    "filterSynthesis": "hourly, daily, weekly",
                    "filterYear": "weekly, monthly, annual",
                    "spreadUnsuppliedEnergyCost": 1400,
                    "spreadSpilledEnergyCost": 0,
                },
            }
        ]

        with requests_mock.Mocker() as mocker:
            areas = json_areas[0]
            areas_1 = json_areas_1[0]
            for area, props in areas.items():
                area_up_props = AreaPropertiesUpdate(**props)  # type: ignore
                dict_areas.update({area: area_up_props})

            mocker.put(url, json=areas_1)  # CamelCase
            self.study.update_areas(dict_areas)

            elec_props = self.study._areas["area_test_1"].properties
            gaz_props = self.study._areas["area_test_2"].properties

            expected_elec = areas[self.area_1]
            expected_gaz = areas[self.area_2]
            assert elec_props.energy_cost_unsupplied == expected_elec["energy_cost_unsupplied"]
            assert gaz_props.energy_cost_unsupplied == expected_gaz["energy_cost_unsupplied"]
            assert elec_props.adequacy_patch_mode.value == expected_elec["adequacy_patch_mode"]
            assert gaz_props.adequacy_patch_mode.value == expected_gaz["adequacy_patch_mode"]
            assert elec_props.dispatch_hydro_power == expected_elec["dispatch_hydro_power"]
            assert gaz_props.dispatch_hydro_power == expected_gaz["dispatch_hydro_power"]

    def test_update_multiple_areas_fail(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/areas"
        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=400, json={"description": self.antares_web_description_msg})

            with pytest.raises(
                AreasPropertiesUpdateError,
                match=f"Could not update areas properties from study '{self.study_id}' : {self.antares_web_description_msg}",
            ):
                self.study.update_areas({})

    def test_update_multiple_links_success(self) -> None:
        updated_links = {}
        self.study._areas["area_test"] = self.area
        self.study._areas["area_test_1"] = self.area_1
        self.study._areas["area_test_2"] = self.area_2

        self.study._links["area_test / area_test_1"] = self.first_link
        self.study._links["area_test / area_test_2"] = self.second_link

        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/links"
        json_update_links = {
            "area_test / area_test_1": {
                "hurdles_cost": False,
                "loop_flow": False,
                "use_phase_shifter": False,
                "transmission_capacities": "enabled",
                "asset_type": "virt",
                "display_comments": True,
                "comments": "",
                "filter_synthesis": "hourly, daily, weekly, monthly, annual",
                "filter_year_by_year": "hourly, daily, weekly, monthly, annual",
                "area1": "area_test",
                "area2": "area_test_1",
            },
            "area_test / area_test_2": {
                "hurdles_cost": False,
                "loop_flow": False,
                "use_phase_shifter": False,
                "transmission_capacities": "enabled",
                "asset_type": "virt",
                "display_comments": True,
                "comments": "",
                "filter_synthesis": "hourly, daily, weekly, monthly, annual",
                "filter_year_by_year": "hourly, daily, weekly, monthly, annual",
                "area1": "area_test",
                "area2": "area_test_2",
            },
        }

        with requests_mock.Mocker() as mocker:
            for link in json_update_links:
                json_update_links[link].pop("area1")
                json_update_links[link].pop("area2")
                link_up = LinkPropertiesUpdate(**json_update_links[link])  # type: ignore
                updated_links.update({link: link_up})
                json_update_links[link].update({"area1": "area_test"})
                json_update_links[link].update({"area2": "area_test_2"})

            mocker.put(url=url, status_code=200, json=json_update_links)
            self.study.update_links(updated_links)
            json_update_links["area_test / area_test_1"].pop("area1")
            json_update_links["area_test / area_test_1"].pop("area2")
            json_update_links["area_test / area_test_2"].pop("area1")
            json_update_links["area_test / area_test_2"].pop("area2")

            link_props_1 = LinkProperties(**json_update_links["area_test / area_test_1"])  # type: ignore
            link_props_2 = LinkProperties(**json_update_links["area_test / area_test_2"])  # type: ignore

            test_links_1 = self.study.get_links()["area_test / area_test_1"]
            assert test_links_1.properties.hurdles_cost == link_props_1.hurdles_cost
            assert test_links_1.properties.display_comments == link_props_1.display_comments
            test_links_2 = self.study.get_links()["area_test / area_test_2"]
            assert test_links_2.properties.hurdles_cost == link_props_2.hurdles_cost
            assert test_links_2.properties.display_comments == link_props_2.display_comments

    def test_update_multiple_links_fail(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/links"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=404, json={"description": self.antares_web_description_msg})

            with pytest.raises(
                LinksPropertiesUpdateError,
                match=f"Could not update links properties from study '{self.study_id}' : {self.antares_web_description_msg}",
            ):
                self.study.update_links({})

    def test_update_multiple_binding_constraints_success(self) -> None:
        self.study._binding_constraints["battery_state_evolution"] = self.b_constraint_1
        self.study._binding_constraints["battery_state_update"] = self.b_constraint_2

        dict_binding_constraints = {}

        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/binding-constraints"
        json_binding_constraints = {
            "battery_state_evolution": {"enabled": True, "time_step": "hourly", "operator": "equal", "comments": ""},
            "battery_state_update": {"enabled": True, "time_step": "hourly", "operator": "less", "comments": ""},
        }

        for bc_id in json_binding_constraints:
            operator = "equal" if bc_id == "battery_state_evolution" else "less"
            bc_props = BindingConstraintPropertiesUpdate(
                enabled=True,
                time_step=BindingConstraintFrequency.HOURLY,
                comments="",
                operator=BindingConstraintOperator(operator),
            )
            dict_binding_constraints[bc_id] = bc_props

        with requests_mock.Mocker() as mocker:
            mocker.put(url, json=json_binding_constraints)
            self.study.update_binding_constraints(dict_binding_constraints)

            assert self.b_constraint_1.properties.enabled == dict_binding_constraints["battery_state_evolution"].enabled
            assert (
                self.b_constraint_1.properties.time_step
                == dict_binding_constraints["battery_state_evolution"].time_step
            )

            assert self.b_constraint_2.properties.enabled == dict_binding_constraints["battery_state_update"].enabled
            assert (
                self.b_constraint_2.properties.time_step == dict_binding_constraints["battery_state_update"].time_step
            )

    def test_update_multiple_binding_constraints_fail(self) -> None:
        url = f"https://antares.com/api/v1/studies/{self.study_id}/table-mode/binding-constraints"

        with requests_mock.Mocker() as mocker:
            mocker.put(url, status_code=400, json={"description": self.antares_web_description_msg})

            with pytest.raises(
                ConstraintsPropertiesUpdateError,
                match=f"Could not update binding constraints properties from study '{self.study_id}': {self.antares_web_description_msg}",
            ):
                self.study.update_binding_constraints({})

    def test_get_scenario_builder_success(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/config/scenariobuilder"
            json_builder = {
                "Default Ruleset": {
                    "h": {"west": {"0": 1}},
                    "hl": {"west": {"0": 0.5}},
                    "l": {"west": {"0": 1}},
                    "s": {"west": {"0": 1}},
                    "t": {"west": {"b": {"0": 1}, "p": {"0": 1}, "sb": {"0": 1}}},
                    "w": {"west": {"0": 1}},
                }
            }
            mocker.get(url, json=json_builder, status_code=201)
            self.study._areas = {"west": self.area}
            self.study._settings.general_parameters = GeneralParameters(nb_years=1)
            sc_builder = self.study.get_scenario_builder()
            assert sc_builder.load.get_area("west").get_scenario() == [1]
            assert sc_builder.hydro_initial_level.get_area("west").get_scenario() == [0.5]

    def test_get_scenario_builder_fails(self) -> None:
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/config/scenariobuilder"
            mocker.get(url, status_code=400, json={"description": self.antares_web_description_msg})
            with pytest.raises(
                ScenarioBuilderReadingError,
                match=f"Could not read the scenario builder for study '{self.study_id}': {self.antares_web_description_msg}",
            ):
                self.study.get_scenario_builder()
