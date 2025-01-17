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

import os
import typing as t

from configparser import ConfigParser
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.exceptions.exceptions import ThermalCreationError
from antares.craft.model.hydro import Hydro
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterGroup,
    RenewableClusterProperties,
    RenewableClusterPropertiesLocal,
    TimeSeriesInterpretation,
)
from antares.craft.model.st_storage import STStorage, STStorageGroup, STStorageProperties, STStoragePropertiesLocal
from antares.craft.model.study import read_study_local
from antares.craft.model.thermal import (
    LawOption,
    LocalTSGenerationBehavior,
    ThermalCluster,
    ThermalClusterGroup,
    ThermalClusterProperties,
    ThermalClusterPropertiesLocal,
    ThermalCostGeneration,
)
from antares.craft.tools.ini_tool import IniFile, IniFileTypes
from antares.craft.tools.matrix_tool import df_save
from antares.craft.tools.time_series_tool import TimeSeriesFileType


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
            local_study_w_thermal.service.config.study_path / IniFileTypes.THERMAL_LIST_INI.value.format(area_id="fr")
        )
        expected_areas_ini_path = local_study_w_thermal.service.config.study_path / IniFileTypes.THERMAL_AREAS_INI.value

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
            local_study_w_areas.service.config.study_path, IniFileTypes.THERMAL_LIST_INI, area_id="fr"
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


class TestCreateRenewablesCluster:
    def test_can_create_renewables_cluster(self, local_study_w_thermal):
        # When
        renewable_cluster_name = "renewable cluster"
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(
            renewable_cluster_name, RenewableClusterProperties(), None
        )

        # Then
        assert local_study_w_thermal.get_areas()["fr"].get_renewables()
        assert isinstance(
            local_study_w_thermal.get_areas()["fr"].get_renewables()[renewable_cluster_name], RenewableCluster
        )

    def test_renewable_cluster_has_properties(self, local_study_with_renewable):
        assert (
            local_study_with_renewable.get_areas()["fr"]
            .get_renewables()["renewable cluster"]
            .properties.model_dump(exclude_none=True)
        )

    def test_renewable_cluster_has_correct_default_properties(
        self, local_study_with_renewable, default_renewable_cluster_properties
    ):
        assert (
            local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"].properties
            == default_renewable_cluster_properties
        )

    def test_renewables_list_ini_exists(self, local_study_with_renewable):
        renewables_list_ini = (
            local_study_with_renewable.service.config.study_path
            / IniFileTypes.RENEWABLES_LIST_INI.value.format(area_id="fr")
        )
        assert renewables_list_ini.is_file()

    def test_renewable_list_ini_has_correct_default_values(
        self, default_renewable_cluster_properties, actual_renewable_list_ini
    ):
        # Given
        expected_renewables_list_ini_content = """[renewable cluster]
name = renewable cluster
group = Other RES 1
enabled = true
nominalcapacity = 0.000000
unitcount = 1
ts-interpretation = power-generation

"""
        expected_renewables_list_ini = ConfigParser()
        expected_renewables_list_ini.read_string(expected_renewables_list_ini_content)

        # When
        with actual_renewable_list_ini.ini_path.open() as renewables_list_ini_file:
            actual_renewable_list_ini_content = renewables_list_ini_file.read()

        assert actual_renewable_list_ini_content == expected_renewables_list_ini_content
        assert actual_renewable_list_ini.parsed_ini.sections() == expected_renewables_list_ini.sections()
        assert actual_renewable_list_ini.parsed_ini == expected_renewables_list_ini

    def test_renewable_cluster_and_ini_have_custom_properties(self, local_study_w_thermal):
        # Given
        props = RenewableClusterProperties(
            group=RenewableClusterGroup.WIND_OFF_SHORE, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        args = {"renewable_name": "renewable cluster", **props.model_dump(mode="json", exclude_none=True)}
        custom_properties = RenewableClusterPropertiesLocal.model_validate(args)
        expected_renewables_list_ini_content = """[renewable cluster]
name = renewable cluster
group = Wind Offshore
enabled = true
nominalcapacity = 0.000000
unitcount = 1
ts-interpretation = production-factor

"""
        actual_renewable_list_ini = IniFile(
            local_study_w_thermal.service.config.study_path, IniFileTypes.RENEWABLES_LIST_INI, area_id="fr"
        )

        # When
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(
            renewable_name=custom_properties.renewable_name,
            properties=custom_properties.yield_renewable_cluster_properties(),
            series=None,
        )
        with actual_renewable_list_ini.ini_path.open() as renewables_list_ini_file:
            actual_renewable_list_ini_content = renewables_list_ini_file.read()

        assert (
            local_study_w_thermal.get_areas()["fr"].get_renewables()["renewable cluster"].properties
            == custom_properties.yield_renewable_cluster_properties()
        )
        assert actual_renewable_list_ini_content == expected_renewables_list_ini_content


class TestCreateSTStorage:
    def test_can_create_st_storage(self, local_study_with_renewable):
        # When
        storage_name = "short term storage"
        local_study_with_renewable.get_areas()["fr"].create_st_storage(storage_name)

        # Then
        assert local_study_with_renewable.get_areas()["fr"].get_st_storages()
        assert isinstance(local_study_with_renewable.get_areas()["fr"].get_st_storages()[storage_name], STStorage)

    def test_storage_has_properties(self, local_study_with_st_storage):
        assert (
            local_study_with_st_storage.get_areas()["fr"]
            .get_st_storages()["short term storage"]
            .properties.model_dump(exclude_none=True)
        )

    def test_storage_has_correct_default_properties(self, local_study_with_st_storage, default_st_storage_properties):
        assert (
            local_study_with_st_storage.get_areas()["fr"].get_st_storages()["short term storage"].properties
            == default_st_storage_properties
        )

    def test_st_storage_list_ini_exists(self, local_study_with_st_storage):
        st_storage_list_ini = (
            local_study_with_st_storage.service.config.study_path
            / IniFileTypes.ST_STORAGE_LIST_INI.value.format(area_id="fr")
        )
        assert st_storage_list_ini.is_file()

    def test_st_storage_list_ini_has_correct_default_values(
        self, default_st_storage_properties, actual_st_storage_list_ini
    ):
        # Given
        expected_st_storage_list_ini_content = """[short term storage]
name = short term storage
group = Other1
injectionnominalcapacity = 0.000000
withdrawalnominalcapacity = 0.000000
reservoircapacity = 0.000000
efficiency = 1.000000
initiallevel = 0.500000
initialleveloptim = false
enabled = true

"""
        expected_st_storage_list_ini = ConfigParser()
        expected_st_storage_list_ini.read_string(expected_st_storage_list_ini_content)

        # When
        with actual_st_storage_list_ini.ini_path.open() as st_storage_list_ini_file:
            actual_st_storage_list_ini_content = st_storage_list_ini_file.read()

        assert actual_st_storage_list_ini_content == expected_st_storage_list_ini_content
        assert actual_st_storage_list_ini.parsed_ini.sections() == expected_st_storage_list_ini.sections()
        assert actual_st_storage_list_ini.parsed_ini == expected_st_storage_list_ini

    def test_st_storage_and_ini_have_custom_properties(self, local_study_w_areas):
        # Given
        props = STStorageProperties(group=STStorageGroup.BATTERY, reservoir_capacity=12.345)
        args = {"st_storage_name": "short term storage", **props.model_dump(mode="json", exclude_none=True)}
        custom_properties = STStoragePropertiesLocal.model_validate(args)
        expected_st_storage_list_ini_content = """[short term storage]
name = short term storage
group = Battery
injectionnominalcapacity = 0.000000
withdrawalnominalcapacity = 0.000000
reservoircapacity = 12.345000
efficiency = 1.000000
initiallevel = 0.500000
initialleveloptim = false
enabled = true

"""
        actual_st_storage_list_ini = IniFile(
            local_study_w_areas.service.config.study_path, IniFileTypes.ST_STORAGE_LIST_INI, area_id="fr"
        )

        # When
        local_study_w_areas.get_areas()["fr"].create_st_storage(
            st_storage_name=custom_properties.st_storage_name,
            properties=custom_properties.yield_st_storage_properties(),
        )
        with actual_st_storage_list_ini.ini_path.open() as st_storage_list_ini_file:
            actual_st_storage_list_ini_content = st_storage_list_ini_file.read()

        assert (
            local_study_w_areas.get_areas()["fr"].get_st_storages()["short term storage"].properties
            == custom_properties.yield_st_storage_properties()
        )
        assert actual_st_storage_list_ini_content == expected_st_storage_list_ini_content


class TestCreateHydro:
    def test_can_create_hydro(self, local_study_with_st_storage):
        # When
        local_study_with_st_storage.get_areas()["fr"].create_hydro()

        # Then
        assert local_study_with_st_storage.get_areas()["fr"].hydro
        assert isinstance(local_study_with_st_storage.get_areas()["fr"].hydro, Hydro)

    def test_hydro_has_properties(self, local_study_w_areas):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties

    def test_hydro_has_correct_default_properties(self, local_study_w_areas, default_hydro_properties):
        assert local_study_w_areas.get_areas()["fr"].hydro.properties == default_hydro_properties

    def test_hydro_ini_exists(self, local_study_w_areas):
        hydro_ini = local_study_w_areas.service.config.study_path / IniFileTypes.HYDRO_INI.value
        assert hydro_ini.is_file()

    def test_hydro_ini_has_correct_default_values(self, local_study_w_areas):
        # Given
        expected_hydro_ini_content = """[inter-daily-breakdown]
fr = 1.000000
it = 1.000000

[intra-daily-modulation]
fr = 24.000000
it = 24.000000

[inter-monthly-breakdown]
fr = 1.000000
it = 1.000000

[reservoir]
fr = false
it = false

[reservoir capacity]
fr = 0.000000
it = 0.000000

[follow load]
fr = true
it = true

[use water]
fr = false
it = false

[hard bounds]
fr = false
it = false

[initialize reservoir date]
fr = 0
it = 0

[use heuristic]
fr = true
it = true

[power to level]
fr = false
it = false

[use leeway]
fr = false
it = false

[leeway low]
fr = 1.000000
it = 1.000000

[leeway up]
fr = 1.000000
it = 1.000000

[pumping efficiency]
fr = 1.000000
it = 1.000000

"""
        expected_hydro_ini = ConfigParser()
        expected_hydro_ini.read_string(expected_hydro_ini_content)
        actual_hydro_ini = IniFile(local_study_w_areas.service.config.study_path, IniFileTypes.HYDRO_INI)

        # When
        with actual_hydro_ini.ini_path.open() as st_storage_list_ini_file:
            actual_hydro_ini_content = st_storage_list_ini_file.read()

        assert actual_hydro_ini_content == expected_hydro_ini_content
        assert actual_hydro_ini.parsed_ini.sections() == expected_hydro_ini.sections()
        assert actual_hydro_ini.parsed_ini == expected_hydro_ini

    def test_hydro_ini_has_correct_sorted_areas(self, actual_hydro_ini):
        # Given
        expected_hydro_ini_content = """[inter-daily-breakdown]
at = 1.000000
fr = 1.000000
it = 1.000000

[intra-daily-modulation]
at = 24.000000
fr = 24.000000
it = 24.000000

[inter-monthly-breakdown]
at = 1.000000
fr = 1.000000
it = 1.000000

[reservoir]
at = false
fr = false
it = false

[reservoir capacity]
at = 0.000000
fr = 0.000000
it = 0.000000

[follow load]
at = true
fr = true
it = true

[use water]
at = false
fr = false
it = false

[hard bounds]
at = false
fr = false
it = false

[initialize reservoir date]
at = 0
fr = 0
it = 0

[use heuristic]
at = true
fr = true
it = true

[power to level]
at = false
fr = false
it = false

[use leeway]
at = false
fr = false
it = false

[leeway low]
at = 1.000000
fr = 1.000000
it = 1.000000

[leeway up]
at = 1.000000
fr = 1.000000
it = 1.000000

[pumping efficiency]
at = 1.000000
fr = 1.000000
it = 1.000000

"""
        expected_hydro_ini = ConfigParser()
        expected_hydro_ini.read_string(expected_hydro_ini_content)

        # When
        with actual_hydro_ini.ini_path.open() as st_storage_list_ini_file:
            actual_hydro_ini_content = st_storage_list_ini_file.read()

        assert actual_hydro_ini_content == expected_hydro_ini_content
        assert actual_hydro_ini.parsed_ini.sections() == expected_hydro_ini.sections()
        assert actual_hydro_ini.parsed_ini == expected_hydro_ini


class TestCreateReserves:
    def test_can_create_reserves_ts_file(self, area_fr):
        # Given
        reserves_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.RESERVES.value.format(
            area_id=area_fr.id
        )
        expected_reserves_file_path = area_fr._area_service.config.study_path / "input/reserves/fr.txt"

        # When
        area_fr.create_reserves(pd.DataFrame())

        # Then
        assert reserves_file_path == expected_reserves_file_path
        assert reserves_file_path.exists()
        assert reserves_file_path.is_file()

    def test_can_create_reserves_ts_file_with_time_series(self, area_fr):
        # Given
        reserves_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.RESERVES.value.format(
            area_id=area_fr.id
        )
        expected_time_series_string = """1.0\t1.0\t1.0
1.0\t1.0\t1.0
"""
        expected_time_series = pd.read_csv(StringIO(expected_time_series_string), sep="\t", header=None)

        # When
        area_fr.create_reserves(pd.DataFrame(np.ones([2, 3])))
        actual_time_series = pd.read_csv(reserves_file_path, sep="\t", header=None)
        with reserves_file_path.open("r") as reserves_ts_file:
            actual_time_series_string = reserves_ts_file.read()

        # Then
        assert actual_time_series.equals(expected_time_series)
        assert actual_time_series_string == expected_time_series_string


class TestCreateMiscGen:
    def test_can_create_misc_gen_ts_file(self, area_fr):
        # Given
        misc_gen_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.MISC_GEN.value.format(
            area_id=area_fr.id
        )
        expected_misc_gen_file_path = area_fr._area_service.config.study_path / "input/misc-gen/miscgen-fr.txt"

        # When
        area_fr.create_misc_gen(pd.DataFrame())

        # Then
        assert misc_gen_file_path == expected_misc_gen_file_path
        assert misc_gen_file_path.exists()
        assert misc_gen_file_path.is_file()

    def test_can_create_misc_gen_ts_file_with_time_series(self, area_fr):
        # Given
        misc_gen_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.MISC_GEN.value.format(
            area_id=area_fr.id
        )
        expected_time_series_string = """1.0\t1.0\t1.0
1.0\t1.0\t1.0
"""
        expected_time_series = pd.read_csv(StringIO(expected_time_series_string), sep="\t", header=None)

        # When
        area_fr.create_misc_gen(pd.DataFrame(np.ones([2, 3])))
        actual_time_series = pd.read_csv(misc_gen_file_path, sep="\t", header=None)
        with misc_gen_file_path.open("r") as misc_gen_ts_file:
            actual_time_series_string = misc_gen_ts_file.read()

        # Then
        assert actual_time_series.equals(expected_time_series)
        assert actual_time_series_string == expected_time_series_string


class TestCreateWind:
    def test_can_create_wind_ts_file(self, area_fr):
        # Given
        wind_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND.value.format(
            area_id=area_fr.id
        )
        expected_wind_file_path = area_fr._area_service.config.study_path / "input/wind/series/wind_fr.txt"

        # When
        area_fr.create_wind(pd.DataFrame())

        # Then
        assert wind_file_path == expected_wind_file_path
        assert wind_file_path.exists()
        assert wind_file_path.is_file()

    def test_can_create_wind_ts_file_with_time_series(self, area_fr):
        # Given
        wind_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND.value.format(
            area_id=area_fr.id
        )
        expected_time_series_string = """1.0\t1.0\t1.0
1.0\t1.0\t1.0
"""
        expected_time_series = pd.read_csv(StringIO(expected_time_series_string), sep="\t", header=None)

        # When
        area_fr.create_wind(pd.DataFrame(np.ones([2, 3])))
        actual_time_series = pd.read_csv(wind_file_path, sep="\t", header=None)
        with wind_file_path.open("r") as wind_ts_file:
            actual_time_series_string = wind_ts_file.read()

        # Then
        assert actual_time_series.equals(expected_time_series)
        assert actual_time_series_string == expected_time_series_string

    def test_settings_ini_exists(self, area_fr, fr_wind):
        # Given
        expected_ini_path = area_fr._area_service.config.study_path / "input/wind/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study, fr_wind):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_data_txt_has_correct_default_values(self, local_study, fr_wind):
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study, fr_wind):
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""

    def test_translation_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_TRANSLATION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()


class TestCreateSolar:
    def test_can_create_solar_ts_file(self, area_fr):
        # Given
        solar_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR.value.format(
            area_id=area_fr.id
        )
        expected_solar_file_path = area_fr._area_service.config.study_path / "input/solar/series/solar_fr.txt"

        # When
        area_fr.create_solar(pd.DataFrame())

        # Then
        assert solar_file_path == expected_solar_file_path
        assert solar_file_path.exists()
        assert solar_file_path.is_file()

    def test_can_create_solar_ts_file_with_time_series(self, area_fr):
        # Given
        solar_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR.value.format(
            area_id=area_fr.id
        )
        expected_time_series_string = """1.0\t1.0\t1.0
1.0\t1.0\t1.0
"""
        expected_time_series = pd.read_csv(StringIO(expected_time_series_string), sep="\t", header=None)

        # When
        area_fr.create_solar(pd.DataFrame(np.ones([2, 3])))
        actual_time_series = pd.read_csv(solar_file_path, sep="\t", header=None)
        with solar_file_path.open("r") as solar_ts_file:
            actual_time_series_string = solar_ts_file.read()

        # Then
        assert actual_time_series.equals(expected_time_series)
        assert actual_time_series_string == expected_time_series_string

    def test_settings_ini_exists(self, area_fr, fr_solar):
        # Given
        expected_ini_path = area_fr._area_service.config.study_path / "input/solar/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study, fr_solar):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_data_txt_has_correct_default_values(self, local_study, fr_solar):
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study, fr_solar):
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""

    def test_translation_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = (
            area_fr._area_service.config.study_path
            / TimeSeriesFileType.SOLAR_TRANSLATION.value.format(area_id=area_fr.id)
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()


class TestCreateLoad:
    def test_can_create_load_ts_file(self, area_fr):
        # Given
        load_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD.value.format(
            area_id=area_fr.id
        )
        expected_load_file_path = area_fr._area_service.config.study_path / "input/load/series/load_fr.txt"

        # When
        area_fr.create_load(pd.DataFrame())

        # Then
        assert load_file_path == expected_load_file_path
        assert load_file_path.exists()
        assert load_file_path.is_file()

    def test_can_create_load_ts_file_with_time_series(self, area_fr):
        # Given
        load_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD.value.format(
            area_id=area_fr.id
        )
        expected_time_series_string = """1.0\t1.0\t1.0
1.0\t1.0\t1.0
"""
        expected_time_series = pd.read_csv(StringIO(expected_time_series_string), sep="\t", header=None)

        # When
        area_fr.create_load(pd.DataFrame(np.ones([2, 3])))
        actual_time_series = pd.read_csv(load_file_path, sep="\t", header=None)
        with load_file_path.open("r") as load_ts_file:
            actual_time_series_string = load_ts_file.read()

        # Then
        assert actual_time_series.equals(expected_time_series)
        assert actual_time_series_string == expected_time_series_string

    def test_settings_ini_exists(self, area_fr, fr_load):
        # Given
        expected_ini_path = area_fr._area_service.config.study_path / "input/load/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study, fr_load):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_data_txt_has_correct_default_values(self, local_study, fr_load):
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_translation_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_TRANSLATION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study, fr_load):
        local_config = t.cast(LocalConfiguration, local_study.service.config)
        study_path = local_config.study_path
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""


class TestReadArea:
    def test_read_areas_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path

        local_study_object = read_study_local(study_path)

        actual_areas = local_study_object.read_areas()
        expected_areas = ["at", "it", "fr"]
        for area in actual_areas:
            assert area.ui.color_rgb == [230, 108, 44]
            assert area.properties.energy_cost_spilled == 0.0
            assert area.properties.energy_cost_unsupplied == 0.0
            assert area.id in expected_areas


def _write_file(_file_path, _time_series) -> None:
    _file_path.parent.mkdir(parents=True, exist_ok=True)
    _time_series.to_csv(_file_path, sep="\t", header=False, index=False, encoding="utf-8")


class TestReadLoad:
    def test_read_load_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            file_path = study_path / "input" / "load" / "series" / f"load_{area.id}.txt"
            _write_file(file_path, expected_time_serie)

            matrix = area.get_load_matrix()
            pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)

        expected_time_serie = pd.DataFrame([])
        for area in areas:
            file_path = study_path / "input" / "load" / "series" / f"load_{area.id}.txt"
            _write_file(file_path, expected_time_serie)
            matrix = area.get_load_matrix()
            pd.testing.assert_frame_equal(matrix, expected_time_serie)


class TestReadRenewable:
    def test_read_renewable_local(self, local_study_with_renewable):
        study_path = local_study_with_renewable.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )
            renewable_list = area.read_renewables()

            if renewable_list:
                assert area.id == "fr"
                assert isinstance(renewable_list, list)
                assert isinstance(renewable_list[0], RenewableCluster)

            for renewable in renewable_list:
                assert renewable.name == "renewable cluster"
                assert renewable.properties.unit_count == 1
                assert renewable.properties.ts_interpretation.value == "power-generation"
                assert renewable.properties.nominal_capacity == 0.000000
                assert renewable.properties.enabled
                assert renewable.properties.group.value == "Other RES 1"

                # Create folder and file for timeserie.
                cluster_path = study_path / "input" / "renewables" / "series" / Path(area.id) / Path(renewable.id)
                os.makedirs(cluster_path, exist_ok=True)
                series_path = cluster_path / "series.txt"
                _write_file(series_path, expected_time_serie)

                # Check matrix
                matrix = renewable.get_timeseries()
                pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)


class TestReadSolar:
    def test_read_solar_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            file_path = study_path / "input" / "solar" / "series" / f"solar_{area.id}.txt"
            _write_file(file_path, expected_time_serie)

            matrix = area.get_solar_matrix()
            pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)

        expected_time_serie = pd.DataFrame([])
        for area in areas:
            file_path = study_path / "input" / "solar" / "series" / f"solar_{area.id}.txt"
            _write_file(file_path, expected_time_serie)
            matrix = area.get_solar_matrix()
            pd.testing.assert_frame_equal(matrix, expected_time_serie)


class TestReadReserves:
    def test_read_reserve_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            file_path = study_path / "input" / "reserves" / f"{area.id}.txt"
            _write_file(file_path, expected_time_serie)

            matrix = area.get_reserves_matrix()
            pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)

        expected_time_serie = pd.DataFrame([])
        for area in areas:
            file_path = study_path / "input" / "reserves" / f"{area.id}.txt"
            _write_file(file_path, expected_time_serie)
            matrix = area.get_reserves_matrix()
            pd.testing.assert_frame_equal(matrix, expected_time_serie)


class TestReadWind:
    def test_read_wind_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            file_path = study_path / "input" / "wind" / "series" / f"wind_{area.id}.txt"
            _write_file(file_path, expected_time_serie)

            matrix = area.get_wind_matrix()
            pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)

        expected_time_serie = pd.DataFrame([])
        for area in areas:
            file_path = study_path / "input" / "wind" / "series" / f"wind_{area.id}.txt"
            _write_file(file_path, expected_time_serie)
            matrix = area.get_wind_matrix()
            pd.testing.assert_frame_equal(matrix, expected_time_serie)


class TestReadmisc_gen:
    def test_read_misc_gen_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            file_path = study_path / "input" / "misc-gen" / f"miscgen-{area.id}.txt"
            _write_file(file_path, expected_time_serie)

            matrix = area.get_misc_gen_matrix()
            pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)

        expected_time_serie = pd.DataFrame([])
        for area in areas:
            file_path = study_path / "input" / "misc-gen" / f"miscgen-{area.id}.txt"
            _write_file(file_path, expected_time_serie)
            matrix = area.get_misc_gen_matrix()
            pd.testing.assert_frame_equal(matrix, expected_time_serie)


class TestReadThermal:
    def test_read_thermals_local(self, local_study_w_thermal):
        study_path = local_study_w_thermal.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )

            thermals_list = area.read_thermal_clusters()

            if thermals_list:
                assert area.id == "fr"
                assert isinstance(thermals_list, list)
                assert isinstance(thermals_list[0], ThermalCluster)

            for thermal in thermals_list:
                assert thermal.name == "test thermal cluster"
                assert thermal.properties.group.value == "Other 1"
                assert thermal.properties.unit_count == 1
                assert thermal.properties.efficiency == 100.000000
                assert thermal.properties.nominal_capacity == 0.000000
                assert thermal.properties.enabled
                assert thermal.properties.cost_generation.value == "SetManually"

                # Create folder and file for timeserie.
                cluster_path = (
                    study_path / "input" / "thermal" / "series" / Path(area.id) / Path(thermal.properties.group.value)
                )
                series_path = cluster_path / "series.txt"
                os.makedirs(cluster_path, exist_ok=True)
                _write_file(series_path, expected_time_serie)

                co2_cost_path = cluster_path / "C02Cost.txt"
                _write_file(co2_cost_path, expected_time_serie)

                fuelCost_path = cluster_path / "fuelCost.txt"
                _write_file(fuelCost_path, expected_time_serie)

                cluster_path = (
                    study_path / "input" / "thermal" / "prepro" / Path(area.id) / Path(thermal.properties.group.value)
                )
                os.makedirs(cluster_path, exist_ok=True)
                series_path_1 = cluster_path / "data.txt"
                series_path_2 = cluster_path / "modulation.txt"
                _write_file(series_path_1, expected_time_serie)
                _write_file(series_path_2, expected_time_serie)

                # Check matrix
                matrix = thermal.get_prepro_data_matrix()
                matrix_1 = thermal.get_prepro_modulation_matrix()
                matrix_2 = thermal.get_series_matrix()
                matrix_3 = thermal.get_co2_cost_matrix()
                matrix_4 = thermal.get_fuel_cost_matrix()

                pd.testing.assert_frame_equal(matrix.astype(str), expected_time_serie.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_1.astype(str), expected_time_serie.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_2.astype(str), expected_time_serie.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_3.astype(str), expected_time_serie.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_4.astype(str), expected_time_serie.astype(str), check_dtype=False)


class TestReadLinks:
    def create_file_with_empty_dataframe(self, file_path: str, df: pd.DataFrame):
        full_path = Path(file_path)

        full_path.parent.mkdir(parents=True, exist_ok=True)
        df_save(df, full_path)

    def test_read_links_local(self, local_study_w_links):
        study_path = local_study_w_links.service.config.study_path
        local_study_object = read_study_local(study_path)

        files_to_write = []
        files_to_write.append(study_path / "input" / "links" / "fr" / "at_parameters.txt")
        files_to_write.append(study_path / "input" / "links" / "fr" / "it_parameters.txt")
        files_to_write.append(study_path / "input" / "links" / "fr" / "capacities" / "at_direct.txt")
        files_to_write.append(study_path / "input" / "links" / "fr" / "capacities" / "at_indirect.txt")
        files_to_write.append(study_path / "input" / "links" / "fr" / "capacities" / "it_direct.txt")
        files_to_write.append(study_path / "input" / "links" / "fr" / "capacities" / "it_indirect.txt")
        df_initial = pd.DataFrame(
            [
                [-1, 0, 0],
                [0, -1, 0],
            ],
            dtype="object",
        )

        for file in files_to_write:
            self.create_file_with_empty_dataframe(file, df_initial)

        links = local_study_object.read_links()

        for link in links:
            if link.area_from_id == "fr":
                matrix = link.get_capacity_direct()
                matrix_2 = link.get_capacity_indirect()
                matrix_3 = link.get_parameters()

                pd.testing.assert_frame_equal(matrix.astype(str), df_initial.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_2.astype(str), df_initial.astype(str), check_dtype=False)
                pd.testing.assert_frame_equal(matrix_3.astype(str), df_initial.astype(str), check_dtype=False)
            assert link.ui.link_style.value == "plain"
            assert link.ui.link_width == 1
            assert link.ui.colorb == 112
            assert link.ui.colorg == 112
            assert link.ui.colorr == 112
            assert not link.properties.hurdles_cost
            assert not link.properties.loop_flow
            assert not link.properties.use_phase_shifter
            assert link.properties.transmission_capacities.value == "enabled"
            assert link.properties.asset_type.value == "ac"
            assert isinstance(link.properties.filter_year_by_year, set)
            assert isinstance(link.properties.filter_synthesis, set)


class TestReadSTstorage:
    def test_read_storage_local(self, local_study_w_thermal):
        # TODO not finished at all, just here to validate area.read_st_storage
        study_path = local_study_w_thermal.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object.read_areas()

        for area in areas:
            with pytest.raises(NotImplementedError):
                area.read_st_storages()
