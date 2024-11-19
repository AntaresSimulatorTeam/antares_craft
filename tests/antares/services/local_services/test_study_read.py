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

import logging
import re

from pathlib import Path
from unittest import mock

from antares.model.hydro import HydroProperties, HydroPropertiesLocal
from antares.model.renewable import (
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesLocal,
    TimeSeriesInterpretation,
)
from antares.model.study import create_study_local, read_study_local

class TestReadStudy:
    def test_directory_not_exists_error(self, caplog):
        study_name = "study_name"

        current_dir = Path.cwd()
        relative_path = Path("fake/path/")
        study_path = current_dir / relative_path
        escaped_full_path = re.escape(str(study_path))

        with caplog.at_level(logging.ERROR):
            with pytest.raises(ValueError, match=escaped_full_path):
                read_study_local(study_name, "880", study_path)

    def test_directory_permission_denied(self, caplog, local_study_with_hydro):
        # Given
        study_name = "studyTest"
        study_path = str(local_study_with_hydro.service.config.study_path).strip("studyTest")
        with caplog.at_level(logging.ERROR):
            with mock.patch(
                "pathlib.Path.iterdir",
                side_effect=PermissionError(f"Some content cannot be accessed in {local_study_with_hydro}"),
            ):
                with pytest.raises(
                    PermissionError,
                    match=f"Some content cannot be accessed in {local_study_with_hydro}",
                ):
                    read_study_local(study_name, "880", study_path)

    def test_read_study_service(self, caplog, local_study_with_hydro):
        study_name = "studyTest"
        area_name = "zone_hs"
        study_path = str(local_study_with_hydro.service.config.study_path).strip(study_name)
        local_study_with_hydro.create_area(area_name)

        patch_ini_path = local_study_with_hydro.service.config.study_path / "patch.json"
        with open(patch_ini_path, "w") as desktop_ini_file:
            content = '{"study": null, "areas": {"zone_hs": {"country": null, "tags": []}}, "thermal_clusters": null, "outputs": null}'
            desktop_ini_file.write(content)

        content = read_study_local(study_name, "880", study_path)
        areas = content.service.read_areas()
        study = content.service.read_study(areas)
        expected_keys = ["areas", "hydro", "load", "misc", "renewables", "solar", "storage", "thermals", "wind"]

        for key in expected_keys:
            assert key in study, f"La clé '{key}' est absente du dictionnaire 'study'"
        not_expected_key = "fake_key"
        assert (
            not_expected_key not in study
        ), f"La clé '{not_expected_key}' ne devrait pas être présente dans le dictionnaire 'study'"

    def test_directory_renewable(self, local_study_w_thermal, actual_renewable_list_ini):
        study_name = "studyTest"
        area_name_1 = "onshore"
        area_name_2 = "offshore"
        study_path = str(local_study_w_thermal.service.config.study_path).strip(study_name)

        props = RenewableClusterProperties(
            group=RenewableClusterGroup.WIND_ON_SHORE, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        args = {"renewable_name": area_name_1, **props.model_dump(mode="json", exclude_none=True)}
        custom_properties = RenewableClusterPropertiesLocal.model_validate(args)
        local_study_w_thermal.create_area(area_name_1)
        local_study_w_thermal.get_areas()[area_name_1].create_renewable_cluster(
            renewable_name=custom_properties.renewable_name,
            properties=custom_properties.yield_renewable_cluster_properties(),
            series=None,
        )

        props = RenewableClusterProperties(
            group=RenewableClusterGroup.WIND_OFF_SHORE, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        args = {"renewable_name": area_name_2, **props.model_dump(mode="json", exclude_none=True)}
        custom_properties = RenewableClusterPropertiesLocal.model_validate(args)
        local_study_w_thermal.create_area(area_name_2)
        local_study_w_thermal.get_areas()[area_name_2].create_renewable_cluster(
            renewable_name=custom_properties.renewable_name,
            properties=custom_properties.yield_renewable_cluster_properties(),
            series=None,
        )

        patch_ini_path = local_study_w_thermal.service.config.study_path / "patch.json"
        with open(patch_ini_path, "w") as desktop_ini_file:
            content = '{"study": null, "areas": {"onshore": {"country": null, "tags": []}, "offshore": {"country": null, "tags": []}}, "thermal_clusters": null, "outputs": null}'
            desktop_ini_file.write(content)

        content = read_study_local(study_name, "880", study_path)
        areas = content.service.read_areas()
        study = content.service.read_study(areas)
        assert study["renewables"].get(area_name_1).get("list") == {
            "onshore": {
                "group": "Wind Onshore",
                "name": "onshore",
                "enabled": "true",
                "unitcount": "1",
                "nominalcapacity": "0.000000",
                "ts-interpretation": "production-factor",
            }
        }
        assert study["renewables"].get(area_name_2).get("list") == {
            "offshore": {
                "name": "offshore",
                "group": "Wind Offshore",
                "enabled": "true",
                "nominalcapacity": "0.000000",
                "unitcount": "1",
                "ts-interpretation": "production-factor",
            }
        }

    def test_directory_hydro(self, local_study_w_thermal):
        study_name = "studyTest"
        area_name = "hydro_1"
        study_path = str(local_study_w_thermal.service.config.study_path).strip(study_name)

        properties = HydroProperties(
            inter_daily_breakdown=6,
            intra_daily_modulation=24,
            inter_monthly_breakdown=1,
            reservoir=False,
            reservoir_capacity=1,
            follow_load=True,
            use_water=False,
            hard_bounds=False,
            initialize_reservoir_date=0,
            use_heuristic=True,
            power_to_level=False,
            use_leeway=False,
            leeway_low=1,
            leeway_up=1,
            pumping_efficiency=1,
        )
        args = {"area_id": area_name, **properties.model_dump(mode="json", exclude_none=True)}
        local_hydro_properties = HydroPropertiesLocal.model_validate(args)
        local_study_w_thermal.create_area(area_name)
        local_study_w_thermal.get_areas()[area_name].create_hydro(
            properties=local_hydro_properties.yield_hydro_properties(),
            matrices=None,
        )

        patch_ini_path = local_study_w_thermal.service.config.study_path / "patch.json"
        with open(patch_ini_path, "w") as desktop_ini_file:
            content = '{"study": null, "areas": {"hydro_1": {"country": null, "tags": []}}, "thermal_clusters": null, "outputs": null}'
            desktop_ini_file.write(content)

        content = read_study_local(study_name, "880", study_path)
        areas = content.service.read_areas()
        study = content.service.read_study(areas)

        assert study["hydro"]["hydro"]["inter-daily-breakdown"]["hydro_1"] == "6.000000"
        assert study["hydro"]["hydro"]["intra-daily-modulation"]["hydro_1"] == "24.000000"
        assert study["hydro"]["hydro"]["inter-monthly-breakdown"]["hydro_1"] == "1.000000"
        assert study["hydro"]["hydro"]["reservoir"]["hydro_1"] == "false"
        assert study["hydro"]["hydro"]["reservoir capacity"]["hydro_1"] == "1.000000"
        assert study["hydro"]["hydro"]["follow load"]["hydro_1"] == "true"
        assert study["hydro"]["hydro"]["use water"]["hydro_1"] == "false"
        assert study["hydro"]["hydro"]["hard bounds"]["hydro_1"] == "false"
        assert study["hydro"]["hydro"]["initialize reservoir date"]["hydro_1"] == "0"
        assert study["hydro"]["hydro"]["use heuristic"]["hydro_1"] == "true"
        assert study["hydro"]["hydro"]["power to level"]["hydro_1"] == "false"
        assert study["hydro"]["hydro"]["use leeway"]["hydro_1"] == "false"
        assert study["hydro"]["hydro"]["leeway up"]["hydro_1"] == "1.000000"
        assert study["hydro"]["hydro"]["pumping efficiency"]["hydro_1"] == "1.000000"

    def test_directory(self, local_study_w_thermal):
        study_name = "studyTest"
        area_name = "hydro_1"

        base_dir = local_study_w_thermal.service.config.study_path
        test_create = create_study_local(study_name, "880", base_dir)

        at = test_create.create_area("at")
        fr = test_create.create_area("fr")
        test_create.create_link(area_from=at, area_to=fr, existing_areas=test_create.get_areas())
        test_read = read_study_local(study_name, "880", base_dir)
        print("comparaison entre deux constructeurs: ", test_read.name, test_create.name, test_read.version, test_create.version)

        assert test_create == test_read

        print("1", test_create.get_areas())
        print("2", test_read.get_areas())
        print("0", test_create.get_areas() == test_read.get_areas())

        print("3", test_create.get_links())
        print("4", test_read.get_links())