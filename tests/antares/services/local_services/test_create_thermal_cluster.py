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

from configparser import ConfigParser
from pathlib import Path

from antares.craft.exceptions.exceptions import ThermalCreationError
from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesLocal,
    ThermalCostGeneration,
)
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


class TestCreateThermalCluster:
    def test_can_be_created(self, local_study_w_areas):
        # Given
        thermal_name = "test_thermal_cluster"

        # When
        created_thermal = local_study_w_areas.get_areas()["fr"].create_thermal_cluster(thermal_name)
        assert isinstance(created_thermal, ThermalCluster)

    def test_duplicate_name_errors(self, local_study_w_thermal):
        # Given
        area_name = "fr"
        thermal_name = "test thermal cluster"

        # Then
        with pytest.raises(
            ThermalCreationError,
            match=f"Could not create the thermal cluster {thermal_name} inside area {area_name}: A thermal cluster called '{thermal_name}' already exists in area '{area_name}'.",
        ):
            local_study_w_thermal.get_areas()[area_name].create_thermal_cluster(thermal_name)

    def test_has_default_properties(self, local_study_w_thermal):
        assert (
            local_study_w_thermal.get_areas()["fr"]
            .get_thermals()["test thermal cluster"]
            .properties.model_dump(exclude_none=True)
        )

    def test_has_correct_default_properties(self, local_study_w_thermal, default_thermal_cluster_properties):
        # Given
        expected_thermal_cluster_properties = default_thermal_cluster_properties

        # When
        actual_thermal_cluster_properties = (
            local_study_w_thermal.get_areas()["fr"].get_thermals()["test thermal cluster"].properties
        )

        assert expected_thermal_cluster_properties == actual_thermal_cluster_properties

    def test_required_ini_files_exist(self, tmp_path, local_study_w_thermal):
        # Given
        expected_list_ini_path = (
            local_study_w_thermal.service.config.study_path
            / InitializationFilesTypes.THERMAL_LIST_INI.value.format(area_id="fr")
        )
        expected_areas_ini_path = (
            local_study_w_thermal.service.config.study_path / InitializationFilesTypes.THERMAL_AREAS_INI.value
        )

        # Then
        assert expected_list_ini_path.is_file()
        assert expected_areas_ini_path.is_file()

    def test_list_ini_has_default_properties(self, tmp_path, local_study_w_thermal, actual_thermal_list_ini):
        # Given
        expected_list_ini_contents = """[test thermal cluster]
group = Other 1
name = test thermal cluster
enabled = True
unitcount = 1
nominalcapacity = 0.000000
gen-ts = use global
min-stable-power = 0.000000
min-up-time = 1
min-down-time = 1
must-run = False
spinning = 0.000000
volatility.forced = 0.000000
volatility.planned = 0.000000
law.forced = uniform
law.planned = uniform
marginal-cost = 0.000000
spread-cost = 0.000000
fixed-cost = 0.000000
startup-cost = 0.000000
market-bid-cost = 0.000000
co2 = 0.000000
nh3 = 0.000000
so2 = 0.000000
nox = 0.000000
pm2_5 = 0.000000
pm5 = 0.000000
pm10 = 0.000000
nmvoc = 0.000000
op1 = 0.000000
op2 = 0.000000
op3 = 0.000000
op4 = 0.000000
op5 = 0.000000
costgeneration = SetManually
efficiency = 100.000000
variableomcost = 0.000000

"""
        expected_list_ini = ConfigParser()
        expected_list_ini.read_string(expected_list_ini_contents)
        with actual_thermal_list_ini.ini_path.open("r") as actual_list_ini_file:
            actual_list_ini_contents = actual_list_ini_file.read()

        # Then
        assert actual_thermal_list_ini.parsed_ini.sections() == expected_list_ini.sections()
        assert actual_list_ini_contents == expected_list_ini_contents
        assert actual_thermal_list_ini.parsed_ini == expected_list_ini

    def test_list_ini_has_custom_properties(self, tmp_path, local_study_w_areas):
        # Given
        expected_list_ini_contents = """[test thermal cluster]
group = Nuclear
name = test thermal cluster
enabled = False
unitcount = 12
nominalcapacity = 3.900000
gen-ts = force no generation
min-stable-power = 3.100000
min-up-time = 3
min-down-time = 2
must-run = True
spinning = 2.300000
volatility.forced = 3.500000
volatility.planned = 3.700000
law.forced = geometric
law.planned = geometric
marginal-cost = 2.900000
spread-cost = 4.200000
fixed-cost = 3.600000
startup-cost = 0.700000
market-bid-cost = 0.800000
co2 = 1.000000
nh3 = 2.000000
so2 = 3.000000
nox = 4.000000
pm2_5 = 5.000000
pm5 = 6.000000
pm10 = 7.000000
nmvoc = 8.000000
op1 = 9.000000
op2 = 10.000000
op3 = 11.000000
op4 = 12.000000
op5 = 13.000000
costgeneration = useCostTimeseries
efficiency = 123.400000
variableomcost = 5.000000

"""
        expected_list_ini = ConfigParser()
        expected_list_ini.read_string(expected_list_ini_contents)
        thermal_cluster_properties = ThermalClusterProperties(
            group=ThermalClusterGroup.NUCLEAR,
            enabled=False,
            unit_count=12,
            nominal_capacity=3.9,
            gen_ts=LocalTSGenerationBehavior.FORCE_NO_GENERATION,
            min_stable_power=3.1,
            min_up_time=3,
            min_down_time=2,
            must_run=True,
            spinning=2.3,
            volatility_forced=3.5,
            volatility_planned=3.7,
            law_forced=LawOption.GEOMETRIC,
            law_planned=LawOption.GEOMETRIC,
            marginal_cost=2.9,
            spread_cost=4.2,
            fixed_cost=3.6,
            startup_cost=0.7,
            market_bid_cost=0.8,
            co2=1.0,
            nh3=2.0,
            so2=3.0,
            nox=4.0,
            pm2_5=5.0,
            pm5=6.0,
            pm10=7.0,
            nmvoc=8.0,
            op1=9.0,
            op2=10.0,
            op3=11.0,
            op4=12.0,
            op5=13.0,
            cost_generation=ThermalCostGeneration.USE_COST_TIME_SERIES,
            efficiency=123.4,
            variable_o_m_cost=5.0,
        )

        # When
        local_study_w_areas.get_areas()["fr"].create_thermal_cluster("test thermal cluster", thermal_cluster_properties)
        actual_thermal_list_ini = IniFile(
            local_study_w_areas.service.config.study_path, InitializationFilesTypes.THERMAL_LIST_INI, area_id="fr"
        )
        actual_thermal_list_ini.update_from_ini_file()
        with actual_thermal_list_ini.ini_path.open("r") as actual_list_ini_file:
            actual_list_ini_contents = actual_list_ini_file.read()

        # Then
        assert actual_thermal_list_ini.parsed_ini.sections() == expected_list_ini.sections()
        assert actual_list_ini_contents == expected_list_ini_contents
        assert actual_thermal_list_ini.parsed_ini == expected_list_ini

    def test_list_ini_has_multiple_clusters(
        self, local_study_w_thermal, actual_thermal_list_ini, default_thermal_cluster_properties
    ):
        # Given
        local_study_w_thermal.get_areas()["fr"].create_thermal_cluster("test thermal cluster two")
        args = default_thermal_cluster_properties.model_dump(mode="json", exclude_none=True)
        args["thermal_name"] = "test thermal cluster"
        expected_list_ini_dict = ThermalClusterPropertiesLocal.model_validate(args).list_ini_fields
        args["thermal_name"] = "test thermal cluster two"
        expected_list_ini_dict.update(ThermalClusterPropertiesLocal.model_validate(args).list_ini_fields)

        expected_list_ini = ConfigParser()
        expected_list_ini.read_dict(expected_list_ini_dict)

        # When
        actual_thermal_list_ini.update_from_ini_file()

        # Then
        assert actual_thermal_list_ini.parsed_ini.sections() == expected_list_ini.sections()
        assert actual_thermal_list_ini.parsed_ini == expected_list_ini

    def test_clusters_are_alphabetical_in_list_ini(
        self, local_study_w_thermal, actual_thermal_list_ini, default_thermal_cluster_properties
    ):
        # Given
        first_cluster_alphabetically = "a is before b and t"
        second_cluster_alphabetically = "b is after a"

        args = default_thermal_cluster_properties.model_dump(mode="json", exclude_none=True)
        args["thermal_name"] = first_cluster_alphabetically
        expected_list_ini_dict = ThermalClusterPropertiesLocal.model_validate(args).list_ini_fields
        args["thermal_name"] = second_cluster_alphabetically
        expected_list_ini_dict.update(ThermalClusterPropertiesLocal.model_validate(args).list_ini_fields)
        args["thermal_name"] = "test thermal cluster"
        expected_list_ini_dict.update(ThermalClusterPropertiesLocal.model_validate(args).list_ini_fields)
        expected_list_ini = ConfigParser()
        expected_list_ini.read_dict(expected_list_ini_dict)

        # When
        local_study_w_thermal.get_areas()["fr"].create_thermal_cluster(second_cluster_alphabetically)
        local_study_w_thermal.get_areas()["fr"].create_thermal_cluster(first_cluster_alphabetically)
        actual_thermal_list_ini.update_from_ini_file()

        # Then
        assert actual_thermal_list_ini.ini_dict.keys() == expected_list_ini_dict.keys()
        assert actual_thermal_list_ini.parsed_ini.sections() == expected_list_ini.sections()
        assert actual_thermal_list_ini.parsed_ini == expected_list_ini

    def test_create_thermal_initialization_files(self, local_study_w_areas):
        study_path = Path(local_study_w_areas.path)
        areas = local_study_w_areas.get_areas()

        for area_id, area in areas.items():
            area.create_thermal_cluster("cluster_test")

        for area_id in areas.keys():
            expected_paths = [
                study_path / f"input/thermal/prepro/{area_id}/cluster/modulation.txt",
                study_path / f"input/thermal/prepro/{area_id}/cluster/data.txt",
                study_path / f"input/thermal/series/{area_id}/cluster/series.txt",
            ]

            for expected_path in expected_paths:
                assert expected_path.is_file(), f"File not created: {expected_path}"
