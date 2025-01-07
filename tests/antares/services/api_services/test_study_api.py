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
from unittest.mock import Mock, patch

import pandas as pd

from antares.craft.api_conf.api_conf import APIconf
from antares.craft.exceptions.exceptions import (
    AreaCreationError,
    BindingConstraintCreationError,
    LinkCreationError,
    OutputsRetrievalError,
    SimulationFailedError,
    SimulationTimeOutError,
    StudyCreationError,
    StudySettingsUpdateError,
    StudyVariantCreationError,
)
from antares.craft.model.area import Area, AreaProperties, AreaUi
from antares.craft.model.binding_constraint import BindingConstraint, BindingConstraintProperties
from antares.craft.model.hydro import HydroProperties
from antares.craft.model.link import Link, LinkProperties, LinkUi
from antares.craft.model.output import (
    Output,
)
from antares.craft.model.settings.general import GeneralParameters
from antares.craft.model.settings.study_settings import StudySettings
from antares.craft.model.simulation import AntaresSimulationParameters, Job, JobStatus, Solver
from antares.craft.model.study import Study, create_study_api, create_variant_api, read_study_api
from antares.craft.service.api_services.output_api import OutputApiService
from antares.craft.service.service_factory import ServiceFactory


class TestCreateAPI:
    api = APIconf("https://antares.com", "token", verify=False)
    study_id = "22c52f44-4c2a-407b-862b-490887f93dd8"
    antares_web_description_msg = "Mocked Server KO"
    study = Study("TestStudy", "880", ServiceFactory(api, study_id))
    area = Area(
        "area_test",
        ServiceFactory(api, study_id).create_area_service(),
        ServiceFactory(api, study_id).create_st_storage_service(),
        ServiceFactory(api, study_id).create_thermal_service(),
        ServiceFactory(api, study_id).create_renewable_service(),
    )

    def test_create_study_test_ok(self) -> None:
        with requests_mock.Mocker() as mocker:
            expected_url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            mocker.post(expected_url, json=self.study_id, status_code=200)
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.get(config_urls, json={}, status_code=200)
            # When
            study = create_study_api("TestStudy", "880", self.api)

            # Then
            assert len(mocker.request_history) == 8
            assert mocker.request_history[0].url == expected_url
            assert isinstance(study, Study)

    def test_create_study_fails(self):
        with requests_mock.Mocker() as mocker:
            url = "https://antares.com/api/v1/studies?name=TestStudy&version=880"
            study_name = "TestStudy"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                StudyCreationError,
                match=f"Could not create the study {study_name}: {self.antares_web_description_msg}",
            ):
                create_study_api(study_name, "880", self.api)

    def test_update_study_settings_success(self):
        with requests_mock.Mocker() as mocker:
            settings = StudySettings()
            settings.general_parameters = GeneralParameters(mode="Adequacy")
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            mocker.put(config_urls, status_code=200)
            mocker.get(config_urls, json={}, status_code=200)
            self.study.update_settings(settings)

    def test_update_study_settings_fails(self):
        with requests_mock.Mocker() as mocker:
            settings = StudySettings()
            settings.general_parameters = GeneralParameters(mode="Adequacy")
            config_urls = re.compile(f"https://antares.com/api/v1/studies/{self.study_id}/config/.*")
            antares_web_description_msg = "Server KO"
            mocker.put(config_urls, json={"description": antares_web_description_msg}, status_code=404)
            with pytest.raises(
                StudySettingsUpdateError,
                match=f"Could not update settings for study {self.study_id}: {antares_web_description_msg}",
            ):
                self.study.update_settings(settings)

    def test_create_area_success(self):
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"

            url1 = f"{base_url}/studies/{self.study_id}/areas"
            mocker.post(url1, json={"id": area_name}, status_code=201)
            ui_info = {"ui": {"x": 0, "y": 0, "layers": 0, "color_r": 0, "color_g": 0, "color_b": 0}}
            area_ui = {
                **AreaUi(layerX={"1": 0}, layerY={"1": 0}, layerColor={"1": "0"}).model_dump(by_alias=True),
                **ui_info,
            }
            mocker.get(url1, json={area_name: area_ui}, status_code=201)
            url2 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/properties/form"
            url3 = f"{base_url}/studies/{self.study_id}/areas/{area_name}/hydro/form"
            mocker.put(url2, status_code=201)
            mocker.get(url2, json=AreaProperties().model_dump(), status_code=200)
            mocker.get(url3, json=HydroProperties().model_dump())
            area = self.study.create_area(area_name)
        assert isinstance(area, Area)

    def test_create_area_fails(self):
        area_name = "area_test"
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/areas"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)

            with pytest.raises(
                AreaCreationError,
                match=f"Could not create the area {area_name}: {self.antares_web_description_msg}",
            ):
                self.study.create_area(area_name)

    def test_create_link_success(self):
        with requests_mock.Mocker() as mocker:
            base_url = f"https://antares.com/api/v1/studies/{self.study_id}"
            url = f"{base_url}/links"
            mocker.post(url, status_code=200)
            self.study._areas["area"] = Area(
                "area",
                self.study._area_service,
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
            )

            raw_url = f"{base_url}/raw?path=input/links/area/properties/area_to"
            json_response = {**LinkProperties().model_dump(by_alias=True), **LinkUi().model_dump(by_alias=True)}
            mocker.get(raw_url, json=json_response, status_code=200)
            link = self.study.create_link(area_from="area", area_to="area_to")
            assert isinstance(link, Link)

    def test_create_binding_constraint_success(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            json_response = BindingConstraintProperties().model_dump(mode="json", by_alias=True)
            constraint_name = "bc_1"
            mocker.post(url, json={"id": "id", "name": constraint_name, "terms": [], **json_response}, status_code=201)
            constraint = self.study.create_binding_constraint(name=constraint_name)
            assert isinstance(constraint, BindingConstraint)

    def test_create_binding_constraint_fails(self):
        with requests_mock.Mocker() as mocker:
            url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"
            mocker.post(url, json={"description": self.antares_web_description_msg}, status_code=404)
            constraint_name = "bc_1"

            with pytest.raises(
                BindingConstraintCreationError,
                match=f"Could not create the binding constraint {constraint_name}: {self.antares_web_description_msg}",
            ):
                self.study.create_binding_constraint(name=constraint_name)

    def test_read_study_api(self):
        json_study = {
            "id": "22c52f44-4c2a-407b-862b-490887f93dd8",
            "name": "test_read_areas",
            "version": "880",
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

        base_url = "https://antares.com/api/v1"
        url = f"{base_url}/studies/{self.study_id}"
        area_url = f"{url}/areas"
        area_props_url = f"{area_url}/zone/properties/form"
        thermal_url = f"{area_url}/zone/clusters/thermal"
        renewable_url = f"{area_url}/zone/clusters/renewable"
        storage_url = f"{area_url}/zone/storages"
        output_url = f"{url}/outputs"

        with requests_mock.Mocker() as mocker:
            mocker.get(url, json=json_study)
            mocker.get(config_urls, json={})
            mocker.get(area_url, json=json_ui)
            mocker.get(area_props_url, json={})
            mocker.get(renewable_url, json=[])
            mocker.get(thermal_url, json=[])
            mocker.get(storage_url, json=[])
            mocker.get(
                output_url,
                json=[],
            )
            actual_study = read_study_api(self.api, self.study_id)

            expected_study_name = json_study.pop("name")
            expected_study_id = json_study.pop("id")
            expected_study_version = json_study.pop("version")

            expected_study = Study(
                expected_study_name,
                expected_study_version,
                ServiceFactory(self.api, expected_study_id, expected_study_name),
                None,
            )

            assert actual_study.name == expected_study.name
            assert actual_study.version == expected_study.version
            assert actual_study.service.study_id == expected_study.service.study_id

    def test_create_variant_success(self):
        variant_name = "variant_test"
        with requests_mock.Mocker() as mocker:
            base_url = "https://antares.com/api/v1"
            url = f"{base_url}/studies/{self.study_id}/variants?name={variant_name}"
            variant_id = "variant_id"
            mocker.post(url, json=variant_id, status_code=201)

            variant_url = f"{base_url}/studies/{variant_id}"
            mocker.get(variant_url, json={"id": variant_id, "name": variant_name, "version": "880"}, status_code=200)

            config_urls = re.compile(f"{base_url}/studies/{variant_id}/config/.*")
            mocker.get(config_urls, json={}, status_code=200)

            areas_url = f"{base_url}/studies/{variant_id}/areas?ui=true"
            mocker.get(areas_url, json={}, status_code=200)

            output_url = f"{base_url}/studies/{variant_id}/outputs"
            mocker.get(
                output_url,
                json=[],
                status_code=200,
            )

            variant = self.study.create_variant(variant_name)
            variant_from_api = create_variant_api(self.api, self.study_id, variant_name)

            assert isinstance(variant, Study)
            assert isinstance(variant_from_api, Study)
            assert variant.name == variant_name
            assert variant_from_api.name == variant_name
            assert variant.service.study_id == variant_id
            assert variant_from_api.service.study_id == variant_id

    def test_create_variant_fails(self):
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

    def test_create_duplicated_link(self):
        area_a = "area_a"
        area_b = "area_b"

        self.study._areas[area_a] = Area(
            area_a,
            self.study._area_service,
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
        )

        existing_link = Link(area_a, area_b, Mock())
        self.study._links[existing_link.id] = existing_link

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area_a} / {area_b}: A link from {area_a} to {area_b} already exists",
        ):
            self.study.create_link(area_from=area_b, area_to=area_a)

    def test_create_link_unknown_area(self):
        area_from = "area_fr"
        area_to = "area_missing"

        self.study._areas[area_from] = Area(
            area_from,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
        )

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area_from} / {area_to}: {area_to} does not exist",
        ):
            self.study.create_link(area_from=area_from, area_to=area_to)

    def test_create_link_same_area(self):
        area = "area_1"

        self.study._areas[area] = Area(
            area,
            self.study._area_service,
            Mock(),
            Mock(),
            Mock(),
        )

        with pytest.raises(
            LinkCreationError,
            match=f"Could not create the link {area} / {area}: A link cannot start and end at the same area",
        ):
            self.study.create_link(area_from=area, area_to=area)

    def test_run_and_wait_antares_simulation(self):
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

            job = self.study.run_antares_simulation(parameters)
            assert isinstance(job, Job)
            assert job.job_id == job_id
            assert job.status == JobStatus.PENDING

            self.study.wait_job_completion(job, time_out=10)

            assert job.status == JobStatus.SUCCESS

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

    def test_read_outputs(self):
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

            self.study.read_outputs()

            assert len(self.study.get_outputs()) == 2
            output1 = self.study.get_output(json_output[0].get("name"))
            output2 = self.study.get_output(json_output[1].get("name"))
            assert output1.archived == json_output[0].get("archived")
            assert output2.archived == json_output[1].get("archived")

            # ===== FAILING TEST =====
            error_message = f"Couldn't get outputs for study {self.study_id}"
            mocker.get(run_url, json={"description": error_message}, status_code=404)
            with pytest.raises(OutputsRetrievalError, match=error_message):
                self.study.read_outputs()

    def test_read_constraints(self):
        pass
        # with requests_mock.Mocker() as mocker:
        #     run_url = f"https://antares.com/api/v1/studies/{self.study_id}/bindingconstraints"

    def test_output_get_matrix(self):
        with requests_mock.Mocker() as mocker:
            output = Output(
                name="test-output", output_service=OutputApiService(self.api, self.study_id), archived=False
            )
            matrix_url = f"https://antares.com/api/v1/studies/{self.study_id}/raw?path=output/{output.name}/economy/mc-all/grid/links"
            matrix_output = {"columns": ["upstream", "downstream"], "data": [["be", "fr"]]}
            mocker.get(matrix_url, json=matrix_output)

            matrix = output.get_matrix("mc-all/grid/links")
            expected_matrix = pd.DataFrame(data=matrix_output["data"], columns=matrix_output["columns"])
            assert isinstance(matrix, pd.DataFrame)
            assert matrix.equals(expected_matrix)

    def test_output_aggregate_values(self):
        with requests_mock.Mocker() as mocker:
            output = Output(
                name="test-output", output_service=OutputApiService(self.api, self.study_id), archived=False
            )

            # aggregate_values_areas_mc_ind
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/aggregate/mc-ind/{output.name}?query_file=values&frequency=annual&format=csv"
            aggregate_output = """
            link,timeId,FLOW LIN. EXP,FLOW LIN. STD
            be - fr,1,0.000000,0.000000
            be - fr,2,0.000000,0.000000
            """
            mocker.get(aggregate_url, text=aggregate_output)
            aggregated_matrix = output.aggregate_areas_mc_ind("values", "annual")
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_links_mc_ind
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/links/aggregate/mc-ind/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, text=aggregate_output)
            aggregated_matrix = output.aggregate_links_mc_ind("values", "annual", columns_names=["fr"])
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_areas_mc_all
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/areas/aggregate/mc-all/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, text=aggregate_output)
            aggregated_matrix = output.aggregate_areas_mc_all("values", "annual")
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)

            # aggregate_values_links_mc_all
            aggregate_url = f"https://antares.com/api/v1/studies/{self.study_id}/links/aggregate/mc-all/{output.name}?query_file=values&frequency=annual&format=csv"
            mocker.get(aggregate_url, text=aggregate_output)
            aggregated_matrix = output.aggregate_links_mc_all("values", "annual")
            expected_matrix = pd.read_csv(StringIO(aggregate_output))
            assert isinstance(aggregated_matrix, pd.DataFrame)
            assert aggregated_matrix.equals(expected_matrix)
