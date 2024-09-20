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

from configparser import ConfigParser
from io import StringIO

import numpy as np
import pandas as pd

from antares.model.hydro import Hydro
from antares.model.renewable import (
    RenewableClusterProperties,
    RenewableCluster,
    RenewableClusterGroup,
    TimeSeriesInterpretation,
    RenewableClusterPropertiesLocal,
)
from antares.model.st_storage import STStorage, STStoragePropertiesLocal, STStorageProperties, STStorageGroup
from antares.model.thermal import (
    ThermalCluster,
    ThermalClusterProperties,
    ThermalClusterGroup,
    LocalTSGenerationBehavior,
    LawOption,
    ThermalCostGeneration,
    ThermalClusterPropertiesLocal,
)
from antares.tools.ini_tool import IniFileTypes, IniFile
from antares.tools.time_series_tool import TimeSeriesFileType


class TestCreateThermalCluster:
    def test_can_be_created(self, local_study_w_areas):
        # Given
        thermal_name = "test_thermal_cluster"

        # When
        created_thermal = local_study_w_areas.get_areas()["fr"].create_thermal_cluster(thermal_name)
        assert isinstance(created_thermal, ThermalCluster)

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
            local_study_w_thermal.service.config.study_path / IniFileTypes.THERMAL_LIST_INI.value.format(area_name="fr")
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

    def test_list_ini_has_custom_properties(self, tmp_path, local_study_w_areas, actual_thermal_list_ini):
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
            / IniFileTypes.RENEWABLES_LIST_INI.value.format(area_name="fr")
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

    def test_renewable_cluster_and_ini_have_custom_properties(self, local_study_w_thermal, actual_renewable_list_ini):
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
            / IniFileTypes.ST_STORAGE_LIST_INI.value.format(area_name="fr")
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

    def test_st_storage_and_ini_have_custom_properties(self, local_study_with_st_storage, actual_st_storage_list_ini):
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

        # When
        local_study_with_st_storage.get_areas()["fr"].create_st_storage(
            st_storage_name=custom_properties.st_storage_name,
            properties=custom_properties.yield_st_storage_properties(),
        )
        with actual_st_storage_list_ini.ini_path.open() as st_storage_list_ini_file:
            actual_st_storage_list_ini_content = st_storage_list_ini_file.read()

        assert (
            local_study_with_st_storage.get_areas()["fr"].get_st_storages()["short term storage"].properties
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
        area_fr.create_reserves(None)

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
        area_fr.create_misc_gen(None)

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
        area_fr.create_wind(None)

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
        assert expected_ini_path == fr_wind.prepro.settings.ini_path

    def test_conversion_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_wind.prepro.conversion.local_file.file_path == expected_file_path

    def test_conversion_txt_has_correct_default_values(self, area_fr, fr_wind):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        with fr_wind.prepro.conversion.local_file.file_path.open("r") as fr_wind_file:
            actual_file_contents = fr_wind_file.read()
        actual_file_data = fr_wind.prepro.conversion.time_series.astype(str)

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_data_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_wind.prepro.data.local_file.file_path == expected_file_path

    def test_data_txt_has_correct_default_values(self, area_fr, fr_wind):
        # Given
        expected_file_contents = """1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
"""
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None)

        # When
        with fr_wind.prepro.data.local_file.file_path.open("r") as fr_wind_file:
            actual_file_contents = fr_wind_file.read()
        actual_file_data = fr_wind.prepro.data.time_series

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_k_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_wind.prepro.k.local_file.file_path == expected_file_path

    def test_k_txt_is_empty_by_default(self, area_fr, fr_wind):
        # Given
        expected_file_contents = """"""

        # When
        with fr_wind.prepro.k.local_file.file_path.open("r") as fr_wind_file:
            actual_file_contents = fr_wind_file.read()

        # Then
        assert actual_file_contents == expected_file_contents

    def test_translation_txt_exists(self, area_fr, fr_wind):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.WIND_TRANSLATION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_wind.prepro.translation.local_file.file_path == expected_file_path

    def test_translation_txt_is_empty_by_default(self, area_fr, fr_wind):
        # Given
        expected_file_contents = """"""

        # When
        with fr_wind.prepro.translation.local_file.file_path.open("r") as fr_wind_file:
            actual_file_contents = fr_wind_file.read()

        # Then
        assert actual_file_contents == expected_file_contents


class TestCreateSolar:
    def test_can_create_solar_ts_file(self, area_fr):
        # Given
        solar_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR.value.format(
            area_id=area_fr.id
        )
        expected_solar_file_path = area_fr._area_service.config.study_path / "input/solar/series/solar_fr.txt"

        # When
        area_fr.create_solar(None)

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
        assert expected_ini_path == fr_solar.prepro.settings.ini_path

    def test_conversion_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_solar.prepro.conversion.local_file.file_path == expected_file_path

    def test_conversion_txt_has_correct_default_values(self, area_fr, fr_solar):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        with fr_solar.prepro.conversion.local_file.file_path.open("r") as fr_solar_file:
            actual_file_contents = fr_solar_file.read()
        actual_file_data = fr_solar.prepro.conversion.time_series.astype(str)

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_data_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_solar.prepro.data.local_file.file_path == expected_file_path

    def test_data_txt_has_correct_default_values(self, area_fr, fr_solar):
        # Given
        expected_file_contents = """1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
"""
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None)

        # When
        with fr_solar.prepro.data.local_file.file_path.open("r") as fr_solar_file:
            actual_file_contents = fr_solar_file.read()
        actual_file_data = fr_solar.prepro.data.time_series

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_k_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.SOLAR_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_solar.prepro.k.local_file.file_path == expected_file_path

    def test_k_txt_is_empty_by_default(self, area_fr, fr_solar):
        # Given
        expected_file_contents = """"""

        # When
        with fr_solar.prepro.k.local_file.file_path.open("r") as fr_solar_file:
            actual_file_contents = fr_solar_file.read()

        # Then
        assert actual_file_contents == expected_file_contents

    def test_translation_txt_exists(self, area_fr, fr_solar):
        # Given
        expected_file_path = (
            area_fr._area_service.config.study_path
            / TimeSeriesFileType.SOLAR_TRANSLATION.value.format(area_id=area_fr.id)
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_solar.prepro.translation.local_file.file_path == expected_file_path

    def test_translation_txt_is_empty_by_default(self, area_fr, fr_solar):
        # Given
        expected_file_contents = """"""

        # When
        with fr_solar.prepro.translation.local_file.file_path.open("r") as fr_solar_file:
            actual_file_contents = fr_solar_file.read()

        # Then
        assert actual_file_contents == expected_file_contents


class TestCreateLoad:
    def test_can_create_load_ts_file(self, area_fr):
        # Given
        load_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD.value.format(
            area_id=area_fr.id
        )
        expected_load_file_path = area_fr._area_service.config.study_path / "input/load/series/load_fr.txt"

        # When
        area_fr.create_load(None)

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
        assert expected_ini_path == fr_load.prepro.settings.ini_path

    def test_conversion_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_CONVERSION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_load.prepro.conversion.local_file.file_path == expected_file_path

    def test_conversion_txt_has_correct_default_values(self, area_fr, fr_load):
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        with fr_load.prepro.conversion.local_file.file_path.open("r") as fr_load_file:
            actual_file_contents = fr_load_file.read()
        actual_file_data = fr_load.prepro.conversion.time_series.astype(str)

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_data_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_DATA.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_load.prepro.data.local_file.file_path == expected_file_path

    def test_data_txt_has_correct_default_values(self, area_fr, fr_load):
        # Given
        expected_file_contents = """1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
1\t1\t0\t1\t1\t1
"""
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None)

        # When
        with fr_load.prepro.data.local_file.file_path.open("r") as fr_load_file:
            actual_file_contents = fr_load_file.read()
        actual_file_data = fr_load.prepro.data.time_series

        # Then
        assert actual_file_data.equals(expected_file_data)
        assert actual_file_contents == expected_file_contents

    def test_k_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_K.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_load.prepro.k.local_file.file_path == expected_file_path

    def test_k_txt_is_empty_by_default(self, area_fr, fr_load):
        # Given
        expected_file_contents = """"""

        # When
        with fr_load.prepro.k.local_file.file_path.open("r") as fr_load_file:
            actual_file_contents = fr_load_file.read()

        # Then
        assert actual_file_contents == expected_file_contents

    def test_translation_txt_exists(self, area_fr, fr_load):
        # Given
        expected_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.LOAD_TRANSLATION.value.format(
            area_id=area_fr.id
        )

        # Then
        assert expected_file_path.exists()
        assert expected_file_path.is_file()
        assert fr_load.prepro.translation.local_file.file_path == expected_file_path

    def test_translation_txt_is_empty_by_default(self, area_fr, fr_load):
        # Given
        expected_file_contents = """"""

        # When
        with fr_load.prepro.translation.local_file.file_path.open("r") as fr_load_file:
            actual_file_contents = fr_load_file.read()

        # Then
        assert actual_file_contents == expected_file_contents
