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


import os
import typing as t

from configparser import ConfigParser
from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from antares.craft import read_study_local
from antares.craft.config.local_configuration import LocalConfiguration
from antares.craft.model.area import AdequacyPatchMode, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.commons import FilterOption
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterGroup,
    RenewableClusterProperties,
    TimeSeriesInterpretation,
)
from antares.craft.model.st_storage import STStorage, STStorageGroup, STStorageProperties
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes
from antares.craft.tools.time_series_tool import TimeSeriesFileType


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

    def test_renewable_cluster_has_correct_default_properties(self, local_study_with_renewable):
        renewable_cluster = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        assert renewable_cluster.properties == RenewableClusterProperties()

    def test_renewables_list_ini_exists(self, local_study_with_renewable):
        renewables_list_ini = (
            local_study_with_renewable.service.config.study_path
            / InitializationFilesTypes.RENEWABLES_LIST_INI.value.format(area_id="fr")
        )
        assert renewables_list_ini.is_file()

    def test_renewable_list_ini_has_correct_default_values(
        self, default_renewable_cluster_properties, actual_renewable_list_ini
    ):
        # Given
        expected_renewables_list_ini_content = """[renewable cluster]
name = renewable cluster
enabled = True
unitcount = 1
nominalcapacity = 0.0
group = other res 1
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
        renewable_properties = RenewableClusterProperties(
            group=RenewableClusterGroup.WIND_OFF_SHORE, ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
        )
        renewable_name = "renewable cluster"
        expected_renewables_list_ini_content = """[renewable cluster]
name = renewable cluster
enabled = True
unitcount = 1
nominalcapacity = 0.0
group = wind offshore
ts-interpretation = production-factor

"""
        actual_renewable_list_ini = IniFile(
            local_study_w_thermal.service.config.study_path, InitializationFilesTypes.RENEWABLES_LIST_INI, area_id="fr"
        )

        # When
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(renewable_name, renewable_properties, None)
        with actual_renewable_list_ini.ini_path.open() as renewables_list_ini_file:
            actual_renewable_list_ini_content = renewables_list_ini_file.read()

        assert (
            local_study_w_thermal.get_areas()["fr"].get_renewables()["renewable cluster"].properties
            == renewable_properties
        )
        assert actual_renewable_list_ini_content == expected_renewables_list_ini_content

    def test_renewable_cluster_and_series_is_empty(self, local_study_w_thermal):
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(
            "generation_1", RenewableClusterProperties(), series=pd.DataFrame()
        )
        full_path = (
            local_study_w_thermal.service.config.study_path
            / "input"
            / "renewables"
            / "series"
            / "fr"
            / "generation_1"
            / "series.txt"
        )
        assert full_path.exists()
        assert full_path.stat().st_size == 0
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(
            "generation_2", RenewableClusterProperties(), series=None
        )
        full_path = (
            local_study_w_thermal.service.config.study_path
            / "input"
            / "renewables"
            / "series"
            / "fr"
            / "generation_2"
            / "series.txt"
        )
        assert full_path.exists()
        assert full_path.stat().st_size == 0


class TestCreateSTStorage:
    def test_can_create_st_storage(self, local_study_with_renewable):
        # When
        storage_name = "short term storage"
        local_study_with_renewable.get_areas()["fr"].create_st_storage(storage_name)

        # Then
        assert local_study_with_renewable.get_areas()["fr"].get_st_storages()
        assert isinstance(local_study_with_renewable.get_areas()["fr"].get_st_storages()[storage_name], STStorage)

    def test_storage_has_correct_default_properties(self, local_study_with_st_storage):
        st_storage = local_study_with_st_storage.get_areas()["fr"].get_st_storages()["short term storage"]
        assert st_storage.properties == STStorageProperties()

    def test_st_storage_list_ini_exists(self, local_study_with_st_storage):
        st_storage_list_ini = (
            local_study_with_st_storage.service.config.study_path
            / InitializationFilesTypes.ST_STORAGE_LIST_INI.value.format(area_id="fr")
        )
        assert st_storage_list_ini.is_file()

    def test_st_storage_list_ini_has_correct_default_values(
        self, default_st_storage_properties, actual_st_storage_list_ini
    ):
        # Given
        expected_st_storage_list_ini_content = """[short term storage]
name = short term storage
group = other1
injectionnominalcapacity = 0.0
withdrawalnominalcapacity = 0.0
reservoircapacity = 0.0
efficiency = 1.0
initiallevel = 0.5
initialleveloptim = False
enabled = True

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
        properties = STStorageProperties(group=STStorageGroup.BATTERY, reservoir_capacity=12.345)
        st_storage_name = "short term storage"

        # When
        created_storage = local_study_w_areas.get_areas()["fr"].create_st_storage(st_storage_name, properties)

        # Then
        expected_st_storage_list_ini_content = """[short term storage]
name = short term storage
group = battery
injectionnominalcapacity = 0.0
withdrawalnominalcapacity = 0.0
reservoircapacity = 12.345
efficiency = 1.0
initiallevel = 0.5
initialleveloptim = False
enabled = True

"""
        actual_st_storage_list_ini = IniFile(
            local_study_w_areas.service.config.study_path, InitializationFilesTypes.ST_STORAGE_LIST_INI, area_id="fr"
        )

        with actual_st_storage_list_ini.ini_path.open() as st_storage_list_ini_file:
            actual_st_storage_list_ini_content = st_storage_list_ini_file.read()

        assert created_storage.properties == properties
        assert actual_st_storage_list_ini_content == expected_st_storage_list_ini_content


class TestCreateReserves:
    def test_can_create_reserves_ts_file(self, area_fr):
        # Given
        reserves_file_path = area_fr._area_service.config.study_path / TimeSeriesFileType.RESERVES.value.format(
            area_id=area_fr.id
        )
        expected_reserves_file_path = area_fr._area_service.config.study_path / "input/reserves/fr.txt"

        # When
        area_fr.set_reserves(pd.DataFrame())

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
        area_fr.set_reserves(pd.DataFrame(np.ones([2, 3])))
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
        area_fr.set_misc_gen(pd.DataFrame())

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
        area_fr.set_misc_gen(pd.DataFrame(np.ones([2, 3])))
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
        area_fr.set_wind(pd.DataFrame())

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
        area_fr.set_wind(pd.DataFrame(np.ones([2, 3])))
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
        area_fr.set_solar(pd.DataFrame())

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
        area_fr.set_solar(pd.DataFrame(np.ones([2, 3])))
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
        area_fr.set_load(pd.DataFrame())

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
        area_fr.set_load(pd.DataFrame(np.ones([2, 3])))
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

        actual_areas = local_study_object._read_areas()
        expected_areas = ["at", "it", "fr"]
        for area in actual_areas:
            assert area.ui.color_rgb == [230, 108, 44]
            assert area.properties.energy_cost_spilled == 1.0
            assert area.properties.energy_cost_unsupplied == 0.5
            assert area.id in expected_areas

    def test_read_areas_thermal_file(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path

        local_study_object = read_study_local(study_path)
        optimization_path = study_path / "input" / "thermal" / "areas.ini"

        antares_content = """[unserverdenergycost]
fr = 10000.000000
it = 10000.000000

[spilledenergycost]
fr = 10.000000
it = 10000.000000
    """
        with open(optimization_path, "w", encoding="utf-8") as antares_file:
            antares_file.write(antares_content)

        local_study_object._read_areas()
        area_fr = local_study_object.get_areas()["fr"]
        assert area_fr.properties.energy_cost_unsupplied == 10000
        assert area_fr.properties.energy_cost_spilled == 10


def _write_file(_file_path, _time_series) -> None:
    _file_path.parent.mkdir(parents=True, exist_ok=True)
    _time_series.to_csv(_file_path, sep="\t", header=False, index=False, encoding="utf-8")


class TestReadLoad:
    def test_read_load_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object._read_areas()

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


class TestReadRenewable:
    def test_read_renewable_local(self, local_study_with_renewable):
        study_path = local_study_with_renewable.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object._read_areas()

        for area in areas:
            expected_time_serie = pd.DataFrame(
                [
                    [-9999999980506447872, 0, 9999999980506447872],
                    [0, area.id, 0],
                ],
                dtype="object",
            )
            renewable_list = area._read_renewables()

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
                assert renewable.properties.group.value == "other res 1"

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
        areas = local_study_object._read_areas()

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


class TestReadReserves:
    def test_read_reserve_local(self, local_study_w_areas):
        study_path = local_study_w_areas.service.config.study_path
        local_study_object = read_study_local(study_path)
        areas = local_study_object._read_areas()

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


class TestReadWind:
    def test_read_wind_local(self, local_study_w_areas):
        study_path = t.cast(LocalConfiguration, local_study_w_areas.service.config).study_path
        areas = local_study_w_areas._read_areas()

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


class TestReadmisc_gen:
    def test_read_misc_gen_local(self, local_study_w_areas):
        study_path = t.cast(LocalConfiguration, local_study_w_areas.service.config).study_path
        areas = local_study_w_areas._read_areas()

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


class TestReadThermal:
    def test_read_thermals_local(self, local_study_w_thermal):
        areas = local_study_w_thermal._read_areas()

        for area in areas:
            thermals_list = area._read_thermal_clusters()

            for thermal in thermals_list:
                # Check properties
                assert thermal.name == "test thermal cluster"
                assert thermal.properties.group.value == "other 1"
                assert thermal.properties.unit_count == 1
                assert thermal.properties.efficiency == 100.000000
                assert thermal.properties.nominal_capacity == 0.000000
                assert thermal.properties.enabled
                assert thermal.properties.cost_generation.value == "SetManually"

                # Check matrices exist
                thermal.get_prepro_data_matrix()
                thermal.get_prepro_modulation_matrix()
                thermal.get_series_matrix()
                thermal.get_co2_cost_matrix()
                thermal.get_fuel_cost_matrix()


class TestReadLinks:
    def test_read_links_local(self, local_study_w_links):
        links = local_study_w_links._read_links()
        for link in links:
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


class TestReadSTStorage:
    def test_read_st_storage_local(self, local_study_w_storage):
        areas = local_study_w_storage._read_areas()

        for area in areas:
            storages = area._read_st_storages()
            if area.name == "fr":
                assert len(storages) == 1
                storage = storages[0]
                assert storage.name == "sts_1"
                assert storage.properties.efficiency == 0.4
                assert storage.properties.initial_level_optim is True
            else:
                assert storages == []


class TestUpateArea:
    def test_update_properties(self, local_study_w_areas):
        # Checks values before update
        area = local_study_w_areas.get_areas()["fr"]
        current_properties = AreaProperties(energy_cost_spilled=1, energy_cost_unsupplied=0.5)
        assert area.properties == current_properties
        # Updates properties
        update_properties = AreaPropertiesUpdate(
            adequacy_patch_mode=AdequacyPatchMode.VIRTUAL,
            filter_synthesis={FilterOption.DAILY},
            energy_cost_spilled=0.4,
        )
        new_properties = area.update_properties(update_properties)
        expected_properties = AreaProperties(
            adequacy_patch_mode=AdequacyPatchMode.VIRTUAL,
            filter_synthesis={FilterOption.DAILY},
            energy_cost_spilled=0.4,
            energy_cost_unsupplied=0.5,
        )
        assert new_properties == expected_properties
        assert area.properties == expected_properties
        # Asserts the ini files are properly modified
        study_path = Path(local_study_w_areas.path)
        optimization_ini_file = IniFile(study_path, InitializationFilesTypes.AREA_OPTIMIZATION_INI, area.id)
        assert optimization_ini_file.ini_dict == {
            "nodal optimization": {
                "non-dispatchable-power": "True",
                "dispatchable-hydro-power": "True",
                "other-dispatchable-power": "True",
                "spread-unsupplied-energy-cost": "0.0",
                "spread-spilled-energy-cost": "0.0",
            },
            "filtering": {"filter-synthesis": "daily", "filter-year-by-year": "annual, daily, hourly, monthly, weekly"},
        }
        adequacy_ini = IniFile(study_path, InitializationFilesTypes.AREA_ADEQUACY_PATCH_INI, area.id)
        assert adequacy_ini.ini_dict == {"adequacy-patch": {"adequacy-patch-mode": "virtual"}}
        thermal_ini = IniFile(study_path, InitializationFilesTypes.THERMAL_AREAS_INI)
        assert thermal_ini.ini_dict == {
            "unserverdenergycost": {"fr": "0.5", "it": "0.5"},
            "spilledenergycost": {"fr": "0.4", "it": "1.0"},
        }

    def test_update_ui(self, local_study_w_areas):
        # Checks values before update
        area = local_study_w_areas.get_areas()["fr"]
        current_ui = AreaUi()
        assert area.ui == current_ui
        # Updates properties
        update_ui = AreaUiUpdate(x=12, color_rgb=[5, 6, 7])
        new_ui = area.update_ui(update_ui)
        expected_ui = AreaUi(x=12, color_rgb=[5, 6, 7], y=0)
        assert new_ui == expected_ui
        assert area.ui == expected_ui
        # Asserts the ini file is properly modified
        study_path = Path(local_study_w_areas.path)
        ui_ini_file = IniFile(study_path, InitializationFilesTypes.AREA_UI_INI, area.id)
        assert ui_ini_file.ini_dict == {
            "ui": {"x": "12", "y": "0", "color_r": "5", "color_g": "6", "color_b": "7"},
            "layerX": {"0": "12"},
            "layerY": {"0": "0"},
            "layerColor": {"0": "5,6,7"},
        }
