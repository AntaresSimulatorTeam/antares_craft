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

import re
import typing as t

from io import StringIO
from pathlib import Path

import numpy as np
import pandas as pd

from checksumdir import dirhash

from antares.craft import (
    ConstraintTerm,
    LinkData,
    STStoragePropertiesUpdate,
    Study,
    read_study_local,
)
from antares.craft.exceptions.exceptions import (
    InvalidFieldForVersionError,
    MatrixFormatError,
    ReferencedObjectDeletionNotAllowed,
)
from antares.craft.model.area import AdequacyPatchMode, Area, AreaProperties, AreaPropertiesUpdate, AreaUi, AreaUiUpdate
from antares.craft.model.commons import FilterOption
from antares.craft.model.renewable import (
    RenewableCluster,
    RenewableClusterProperties,
    TimeSeriesInterpretation,
)
from antares.craft.model.st_storage import STStorage, STStorageGroup, STStorageProperties
from antares.craft.service.local_services.services.area import AreaLocalService
from antares.craft.tools import matrix_tool
from antares.craft.tools.serde_local.ini_reader import IniReader
from antares.craft.tools.time_series_tool import TimeSeriesFileType
from tests.antares.services.local_services.conftest import RUN_ON_WINDOWS


class TestCreateRenewablesCluster:
    def test_can_create_renewables_cluster(self, local_study_w_thermal: Study) -> None:
        # When
        renewable_cluster_name = "renewable cluster"
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(
            renewable_cluster_name, RenewableClusterProperties()
        )

        # Then
        assert local_study_w_thermal.get_areas()["fr"].get_renewables()
        assert isinstance(
            local_study_w_thermal.get_areas()["fr"].get_renewables()[renewable_cluster_name], RenewableCluster
        )

    def test_renewable_cluster_has_correct_default_properties(self, local_study_with_renewable: Study) -> None:
        renewable_cluster = local_study_with_renewable.get_areas()["fr"].get_renewables()["renewable cluster"]
        assert renewable_cluster.properties == RenewableClusterProperties(enabled=False, unit_count=44)

    def test_renewable_list_ini_has_correct_default_values(self, local_study_with_renewable: Study) -> None:
        # Given
        expected_renewables_list_ini_content = """[renewable cluster]
name = renewable cluster
enabled = False
unitcount = 44
nominalcapacity = 0.0
group = other res 1
ts-interpretation = power-generation

"""
        study_path = Path(local_study_with_renewable.path)
        ini_content = (study_path / "input" / "renewables" / "clusters" / "fr" / "list.ini").read_text()
        assert ini_content == expected_renewables_list_ini_content

    def test_renewable_cluster_and_ini_have_custom_properties(self, local_study_w_thermal: Study) -> None:
        # Given
        renewable_properties = RenewableClusterProperties(
            group="wind offshore", ts_interpretation=TimeSeriesInterpretation.PRODUCTION_FACTOR
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

        # When
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster(renewable_name, renewable_properties)
        study_path = Path(local_study_w_thermal.path)
        ini_content = (study_path / "input" / "renewables" / "clusters" / "fr" / "list.ini").read_text()
        assert ini_content == expected_renewables_list_ini_content

        assert (
            local_study_w_thermal.get_areas()["fr"].get_renewables()["renewable cluster"].properties
            == renewable_properties
        )

    def test_renewable_cluster_and_series_is_empty(self, local_study_w_thermal: Study) -> None:
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster("generation_1", RenewableClusterProperties())
        full_path = (
            Path(local_study_w_thermal.path) / "input" / "renewables" / "series" / "fr" / "generation_1" / "series.txt"
        )
        assert full_path.exists()
        assert full_path.stat().st_size == 0
        local_study_w_thermal.get_areas()["fr"].create_renewable_cluster("generation_2", RenewableClusterProperties())
        full_path = (
            Path(local_study_w_thermal.path) / "input" / "renewables" / "series" / "fr" / "generation_2" / "series.txt"
        )
        assert full_path.exists()
        assert full_path.stat().st_size == 0


class TestCreateSTStorage:
    def test_can_create_st_storage(self, local_study_with_renewable: Study) -> None:
        # When
        storage_name = "short term storage"
        local_study_with_renewable.get_areas()["fr"].create_st_storage(storage_name)

        # Then
        assert local_study_with_renewable.get_areas()["fr"].get_st_storages()
        assert isinstance(local_study_with_renewable.get_areas()["fr"].get_st_storages()[storage_name], STStorage)

    def test_storage_has_correct_default_properties(self, local_study_with_st_storage: Study) -> None:
        st_storage = local_study_with_st_storage.get_areas()["fr"].get_st_storages()["short term storage"]
        assert st_storage.properties == STStorageProperties()

    def test_storage_error_for_custom_group88(self, local_study_with_st_storage: Study) -> None:
        st_storage = local_study_with_st_storage.get_areas()["fr"].get_st_storages()["short term storage"]

        with pytest.raises(
            ValueError,
            match=re.escape(
                "Group 'custom group' for 8.8 has to be a valid value : ['psp_open', 'psp_closed', 'pondage', 'battery', 'other1', 'other2', 'other3', 'other4', 'other5']"
            ),
        ):
            st_storage.update_properties(STStoragePropertiesUpdate(group="custom group"))

    def test_storage_has_correct_default_properties_92(self, local_study_92: Study) -> None:
        st_storage = local_study_92.get_areas()["fr"].create_st_storage("short term storage")

        expected_properties_9_2 = STStorageProperties(
            group=STStorageGroup.OTHER1.value,
            injection_nominal_capacity=0,
            withdrawal_nominal_capacity=0,
            reservoir_capacity=0,
            efficiency=1,
            initial_level=0.5,
            initial_level_optim=False,
            enabled=True,
            efficiency_withdrawal=1.0,
            penalize_variation_injection=False,
            penalize_variation_withdrawal=False,
        )

        assert st_storage.properties == expected_properties_9_2

    def test_st_storage_list_ini_exists(self, local_study_with_st_storage: Study) -> None:
        study_path = Path(local_study_with_st_storage.path)
        assert (study_path / "input" / "st-storage" / "clusters" / "fr" / "list.ini").exists()

    def test_st_storage_and_ini_have_custom_properties(self, local_study_w_areas: Study) -> None:
        # Given
        properties = STStorageProperties(group=STStorageGroup.BATTERY.value, reservoir_capacity=12.345)
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
        study_path = Path(local_study_w_areas.path)
        ini_content = (study_path / "input" / "st-storage" / "clusters" / "fr" / "list.ini").read_text()
        assert ini_content == expected_st_storage_list_ini_content

        assert created_storage.properties == properties

    def test_st_storage_and_ini_raise_error_with_custom_properties_88(self, local_study_w_areas: Study) -> None:
        properties = STStorageProperties(
            group=STStorageGroup.BATTERY.value, reservoir_capacity=12.345, penalize_variation_injection=True
        )
        st_storage_name = "short term storage"

        with pytest.raises(
            InvalidFieldForVersionError,
            match="Field penalize_variation_injection is not a valid field for study version 8.8",
        ):
            local_study_w_areas.get_areas()["fr"].create_st_storage(st_storage_name, properties)

    def test_st_storage_and_ini_have_custom_properties_92(self, local_study_92: Study) -> None:
        # Given
        properties = STStorageProperties(
            group=STStorageGroup.BATTERY.value, reservoir_capacity=12.345, efficiency_withdrawal=3.2
        )
        st_storage_name = "short term storage"

        # When
        created_storage = local_study_92.get_areas()["fr"].create_st_storage(st_storage_name, properties)

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
efficiencywithdrawal = 3.2

"""
        study_path = Path(local_study_92.path)
        ini_content = (study_path / "input" / "st-storage" / "clusters" / "fr" / "list.ini").read_text()
        assert ini_content == expected_st_storage_list_ini_content

        # For version 9.2, default values are set for properties that weren't explicitly provided
        expected_properties = STStorageProperties(
            group=STStorageGroup.BATTERY.value,
            reservoir_capacity=12.345,
            efficiency_withdrawal=3.2,
            penalize_variation_injection=False,
            penalize_variation_withdrawal=False,
        )
        assert created_storage.properties == expected_properties

    def test_creation_default_matrices_92(self, tmp_path: Path, local_study_92: Study) -> None:
        # given
        st_storage_name = "storage_ts"

        # when
        storage = local_study_92.get_areas()["fr"].create_st_storage(st_storage_name)

        # then
        matrix_default = pd.DataFrame(matrix_tool.default_series)
        assert storage.get_cost_injection().equals(matrix_default)
        assert storage.get_cost_withdrawal().equals(matrix_default)
        assert storage.get_cost_level().equals(matrix_default)
        assert storage.get_cost_variation_injection().equals(matrix_default)
        assert storage.get_cost_variation_withdrawal().equals(matrix_default)

    def test_creation_matrices_not_allowed_88(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # given
        st_storage_name = "storage_ts"

        # when
        storage = local_study_w_areas.get_areas()["fr"].create_st_storage(st_storage_name)

        # then
        with pytest.raises(ValueError, match="The matrix cost_injection is not available for study version 8.8"):
            storage.get_cost_injection()
        with pytest.raises(ValueError, match="The matrix cost_withdrawal is not available for study version 8.8"):
            storage.get_cost_withdrawal()
        with pytest.raises(ValueError, match="The matrix cost_level is not available for study version 8.8"):
            storage.get_cost_level()
        with pytest.raises(
            ValueError,
            match="The matrix cost_variation_injection is not available for study version 8.8",
        ):
            storage.get_cost_variation_injection()
        with pytest.raises(
            ValueError,
            match="The matrix cost_variation_withdrawal is not available for study version 8.8",
        ):
            storage.get_cost_variation_withdrawal()

    def test_update_matrices_92(self, tmp_path: Path, local_study_92: Study) -> None:
        # given
        st_storage_name = "storage_ts"

        # when
        storage = local_study_92.get_areas()["fr"].create_st_storage(st_storage_name)

        # then
        matrix = pd.DataFrame(data=8760 * [[3]])
        storage.set_cost_injection(matrix)
        assert storage.get_cost_injection().equals(matrix)
        storage.set_cost_withdrawal(matrix)
        assert storage.get_cost_withdrawal().equals(matrix)
        storage.set_cost_level(matrix)
        assert storage.get_cost_level().equals(matrix)
        storage.set_cost_variation_injection(matrix)
        assert storage.get_cost_variation_injection().equals(matrix)
        storage.set_cost_variation_withdrawal(matrix)
        assert storage.get_cost_variation_withdrawal().equals(matrix)

    def test_update_matrices_88_not_allowed(self, tmp_path: Path, local_study_w_areas: Study) -> None:
        # given
        st_storage_name = "storage_ts"

        # when
        storage = local_study_w_areas.get_areas()["fr"].create_st_storage(st_storage_name)

        # then
        matrix = pd.DataFrame(data=8760 * [[3]])
        with pytest.raises(ValueError, match="The matrix cost_injection is not available for study version 8.8"):
            storage.set_cost_injection(matrix)
        with pytest.raises(ValueError, match="The matrix cost_withdrawal is not available for study version 8.8"):
            storage.set_cost_withdrawal(matrix)
        with pytest.raises(
            ValueError,
            match="The matrix cost_level is not available for study version 8.8",
        ):
            storage.set_cost_level(matrix)
        with pytest.raises(
            ValueError,
            match="The matrix cost_variation_injection is not available for study version 8.8",
        ):
            storage.set_cost_variation_injection(matrix)
        with pytest.raises(
            ValueError,
            match="The matrix cost_variation_withdrawal is not available for study version 8.8",
        ):
            storage.set_cost_variation_withdrawal(matrix)

    def test_update_matrices_wrong_format_92(self, tmp_path: Path, local_study_92: Study) -> None:
        # given
        st_storage_name = "storage_ts"

        # when
        storage = local_study_92.get_areas()["fr"].create_st_storage(st_storage_name)

        # then
        matrix = pd.DataFrame(data=[[1, 2, 3], [4, 5, 6]])
        with pytest.raises(
            MatrixFormatError,
            match=re.escape(
                "Wrong format for storage/fr/storage_ts/cost_injection matrix, expected shape is (8760, 1) and was : (2, 3)"
            ),
        ):
            storage.set_cost_injection(matrix)


class TestCreateReserves:
    def test_can_create_reserves_ts_file(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        reserves_file_path = study_path / TimeSeriesFileType.RESERVES.value.format(area_id=area_fr.id)
        expected_reserves_file_path = study_path / "input/reserves/fr.txt"

        # When
        area_fr.set_reserves(pd.DataFrame())

        # Then
        assert reserves_file_path == expected_reserves_file_path
        assert reserves_file_path.exists()
        assert reserves_file_path.is_file()

    def test_can_create_reserves_ts_file_with_time_series(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        reserves_file_path = study_path / TimeSeriesFileType.RESERVES.value.format(area_id=area_fr.id)
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
    def test_can_create_misc_gen_ts_file(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        misc_gen_file_path = study_path / TimeSeriesFileType.MISC_GEN.value.format(area_id=area_fr.id)
        expected_misc_gen_file_path = study_path / "input/misc-gen/miscgen-fr.txt"

        # When
        area_fr.set_misc_gen(pd.DataFrame())

        # Then
        assert misc_gen_file_path == expected_misc_gen_file_path
        assert misc_gen_file_path.exists()
        assert misc_gen_file_path.is_file()

    def test_can_create_misc_gen_ts_file_with_time_series(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        misc_gen_file_path = study_path / TimeSeriesFileType.MISC_GEN.value.format(area_id=area_fr.id)
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
    def test_can_create_wind_ts_file(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        wind_file_path = study_path / TimeSeriesFileType.WIND.value.format(area_id=area_fr.id)
        expected_wind_file_path = study_path / "input/wind/series/wind_fr.txt"

        # When
        area_fr.set_wind(pd.DataFrame())

        # Then
        assert wind_file_path == expected_wind_file_path
        assert wind_file_path.exists()
        assert wind_file_path.is_file()

    def test_can_create_wind_ts_file_with_time_series(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        wind_file_path = study_path / TimeSeriesFileType.WIND.value.format(area_id=area_fr.id)
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

    def test_settings_ini_exists(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        expected_ini_path = study_path / "input/wind/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "wind" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""


class TestCreateSolar:
    def test_can_create_solar_ts_file(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        solar_file_path = study_path / TimeSeriesFileType.SOLAR.value.format(area_id=area_fr.id)
        expected_solar_file_path = study_path / "input/solar/series/solar_fr.txt"

        # When
        area_fr.set_solar(pd.DataFrame())

        # Then
        assert solar_file_path == expected_solar_file_path
        assert solar_file_path.exists()
        assert solar_file_path.is_file()

    def test_can_create_solar_ts_file_with_time_series(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        solar_file_path = study_path / TimeSeriesFileType.SOLAR.value.format(area_id=area_fr.id)
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

    def test_settings_ini_exists(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        expected_ini_path = study_path / "input/solar/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "solar" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""


class TestCreateLoad:
    def test_can_create_load_ts_file(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        load_file_path = study_path / TimeSeriesFileType.LOAD.value.format(area_id=area_fr.id)
        expected_load_file_path = study_path / "input/load/series/load_fr.txt"

        # When
        area_fr.set_load(pd.DataFrame())

        # Then
        assert load_file_path == expected_load_file_path
        assert load_file_path.exists()
        assert load_file_path.is_file()

    def test_can_create_load_ts_file_with_time_series(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        load_file_path = study_path / TimeSeriesFileType.LOAD.value.format(area_id=area_fr.id)
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

    def test_settings_ini_exists(self, area_fr: Area) -> None:
        # Given
        study_path = t.cast(AreaLocalService, area_fr._area_service).config.study_path
        expected_ini_path = study_path / "input/load/prepro/fr/settings.ini"

        # Then
        assert expected_ini_path.exists()
        assert expected_ini_path.is_file()

    def test_conversion_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_contents = """-9999999980506447872\t0\t9999999980506447872
0\t0\t0
"""
        # data has to be compared as strings as the first value in the first column is too small for python apparently
        expected_file_data = pd.read_csv(StringIO(expected_file_contents), sep="\t", header=None).astype(str)

        # When
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / "conversion.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=str)

        # Then
        assert actual_data.equals(expected_file_data)

    def test_data_txt_has_correct_default_values(self, local_study_w_areas: Study) -> None:
        # Given
        expected_file_data = pd.DataFrame(np.ones([12, 6]), dtype=int)
        expected_file_data[2] = 0

        # Then
        study_path = Path(local_study_w_areas.path)
        actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / "data.txt")
        actual_data = pd.read_csv(actual_file_path, sep="\t", header=None, dtype=int)
        # For some reason the equality check fails on windows, so we check it in a different way
        assert actual_data.to_dict() == expected_file_data.to_dict()

    def test_k_and_translation_txt_is_empty_by_default(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
        for file in ["k", "translation"]:
            actual_file_path = study_path.joinpath(Path("input") / "load" / "prepro" / "fr" / f"{file}.txt")
            assert actual_file_path.read_text() == ""


class TestReadArea:
    def test_read_areas_local(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)

        local_study_object = read_study_local(study_path)

        actual_areas = local_study_object.get_areas()
        expected_areas = ["at", "it", "fr"]
        for area in actual_areas.values():
            assert area.ui.color_rgb == [230, 108, 44]
            assert area.properties.energy_cost_spilled == 1.0
            assert area.properties.energy_cost_unsupplied == 0.5
            assert area.id in expected_areas

    def test_read_areas_thermal_file(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
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

        study = read_study_local(study_path)
        area_fr = study.get_areas()["fr"]
        assert area_fr.properties.energy_cost_unsupplied == 10000
        assert area_fr.properties.energy_cost_spilled == 10


def _write_file(_file_path: Path, _time_series: pd.DataFrame) -> None:
    _file_path.parent.mkdir(parents=True, exist_ok=True)
    _time_series.to_csv(_file_path, sep="\t", header=False, index=False, encoding="utf-8")


class TestReadLoad:
    def test_read_load_local(self, local_study_w_areas: Study) -> None:
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            expected_df = pd.DataFrame(data=np.ones((8760, 6)))
            area.set_load(expected_df)
            matrix = area.get_load_matrix()
            assert matrix.equals(expected_df)


class TestReadRenewable:
    def test_read_renewable_from_study(self, local_study_with_renewable: Study) -> None:
        area = local_study_with_renewable.get_areas()["fr"]

        renewable_list = list(area.get_renewables().values())
        assert len(renewable_list) == 1

        renewable = renewable_list[0]
        assert renewable.name == "renewable cluster"
        assert renewable.properties.unit_count == 44
        assert renewable.properties.ts_interpretation.value == "power-generation"
        assert renewable.properties.nominal_capacity == 0.000000
        assert not renewable.properties.enabled
        assert renewable.properties.group == "other res 1"
        renewable.get_timeseries()

    def test_read_renewable_from_path(self, local_study_with_renewable: Study) -> None:
        study_path = Path(local_study_with_renewable.path)
        local_study_object = read_study_local(study_path)
        area = local_study_object.get_areas()["fr"]

        renewable_list = list(area.get_renewables().values())
        assert len(renewable_list) == 1

        renewable = renewable_list[0]
        assert renewable.name == "renewable cluster"
        assert renewable.properties.unit_count == 44
        assert renewable.properties.ts_interpretation.value == "power-generation"
        assert renewable.properties.nominal_capacity == 0.000000
        assert not renewable.properties.enabled
        assert renewable.properties.group == "other res 1"
        renewable.get_timeseries()


class TestReadSolar:
    def test_read_solar_local(self, local_study_w_areas: Study) -> None:
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            expected_df = pd.DataFrame(data=np.ones((8760, 6)))
            area.set_solar(expected_df)
            matrix = area.get_solar_matrix()
            assert matrix.equals(expected_df)


class TestReadReserves:
    def test_read_reserve_local(self, local_study_w_areas: Study) -> None:
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            expected_df = pd.DataFrame(data=np.ones((8760, 6)))
            area.set_reserves(expected_df)
            matrix = area.get_reserves_matrix()
            assert matrix.equals(expected_df)


class TestReadWind:
    def test_read_wind_local(self, local_study_w_areas: Study) -> None:
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            expected_df = pd.DataFrame(data=np.ones((8760, 6)))
            area.set_wind(expected_df)
            matrix = area.get_wind_matrix()
            assert matrix.equals(expected_df)


class TestReadmisc_gen:
    def test_read_misc_gen_local(self, local_study_w_areas: Study) -> None:
        areas = local_study_w_areas.get_areas()
        for area in areas.values():
            expected_df = pd.DataFrame(data=np.ones((8760, 6)))
            area.set_misc_gen(expected_df)
            matrix = area.get_misc_gen_matrix()
            assert matrix.equals(expected_df)


class TestReadThermal:
    def test_read_thermals_from_study(self, local_study_w_thermal: Study) -> None:
        areas = local_study_w_thermal.get_areas()
        thermal = areas["fr"].get_thermals()["test thermal cluster"]

        # Check properties
        assert thermal.name == "test thermal cluster"
        assert thermal.properties.group == "nuclear"
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

    def test_read_thermals_from_path(self, local_study_w_thermal: Study) -> None:
        study_path = Path(local_study_w_thermal.path)
        local_study_object = read_study_local(study_path)
        areas = local_study_object.get_areas()
        thermal = areas["fr"].get_thermals()["test thermal cluster"]

        assert thermal.name == "test thermal cluster"
        assert thermal.properties.group == "nuclear"
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
    def test_read_links_local(self, local_study_w_links: Study) -> None:
        links = local_study_w_links.get_links()
        for link in links.values():
            assert link.ui.link_style.value == "plain"
            assert link.ui.link_width == 29
            assert link.ui.colorb == 112
            assert link.ui.colorg == 112
            assert link.ui.colorr == 1
            assert not link.properties.hurdles_cost
            assert not link.properties.loop_flow
            assert link.properties.use_phase_shifter
            assert link.properties.transmission_capacities.value == "enabled"
            assert link.properties.asset_type.value == "ac"
            assert link.properties.filter_year_by_year == {
                FilterOption.WEEKLY,
                FilterOption.DAILY,
                FilterOption.HOURLY,
                FilterOption.ANNUAL,
                FilterOption.MONTHLY,
            }
            assert link.properties.filter_synthesis == {FilterOption.WEEKLY}


class TestReadSTStorage:
    def test_read_st_storage_from_study(self, local_study_w_storage: Study) -> None:
        areas = local_study_w_storage.get_areas()

        storages = areas["fr"].get_st_storages()
        assert len(storages) == 2
        storage = storages["sts_1"]
        assert storage.name == "sts_1"
        assert storage.properties.efficiency == 0.4
        assert storage.properties.initial_level_optim is True

    def test_read_st_storage_from_path(self, local_study_w_storage: Study) -> None:
        study_path = Path(local_study_w_storage.path)
        local_study_object = read_study_local(study_path)

        areas = local_study_object.get_areas()
        storage = areas["fr"].get_st_storages()["sts_1"]

        assert storage.properties.efficiency == 0.4
        assert storage.properties.initial_level_optim is True


class TestUpateArea:
    def test_update_properties(self, local_study_w_areas: Study) -> None:
        # Checks values before update
        area = local_study_w_areas.get_areas()["fr"]
        current_properties = AreaProperties(
            energy_cost_spilled=1, energy_cost_unsupplied=0.5, filter_synthesis={FilterOption.WEEKLY}
        )
        assert area.properties == current_properties
        # Updates properties
        update_properties = AreaPropertiesUpdate(
            adequacy_patch_mode=AdequacyPatchMode.VIRTUAL,
            filter_by_year={FilterOption.DAILY},
            energy_cost_spilled=0,
        )
        new_properties = area.update_properties(update_properties)
        expected_properties = AreaProperties(
            adequacy_patch_mode=AdequacyPatchMode.VIRTUAL,
            filter_by_year={FilterOption.DAILY},
            filter_synthesis={FilterOption.WEEKLY},
            energy_cost_spilled=0,
            energy_cost_unsupplied=0.5,
        )
        assert new_properties == expected_properties
        assert area.properties == expected_properties
        # Asserts the ini files are properly modified
        study_path = Path(local_study_w_areas.path)
        optimization_ini = IniReader().read(study_path / "input" / "areas" / area.id / "optimization.ini")
        assert optimization_ini == {
            "nodal optimization": {
                "non-dispatchable-power": True,
                "dispatchable-hydro-power": True,
                "other-dispatchable-power": True,
                "spread-unsupplied-energy-cost": 0,
                "spread-spilled-energy-cost": 0,
            },
            "filtering": {"filter-synthesis": "weekly", "filter-year-by-year": "daily"},
        }
        adequacy_ini = IniReader().read(study_path / "input" / "areas" / area.id / "adequacy_patch.ini")
        assert adequacy_ini == {"adequacy-patch": {"adequacy-patch-mode": "virtual"}}
        thermal_ini = IniReader().read(study_path / "input" / "thermal" / "areas.ini")
        assert thermal_ini == {
            "unserverdenergycost": {"fr": 0.5, "it": 0.5},
            "spilledenergycost": {"fr": 0, "it": 1.0},
        }

    def test_update_ui(self, local_study_w_areas: Study) -> None:
        # Checks values before update
        area = local_study_w_areas.get_areas()["fr"]
        current_ui = AreaUi(x=56)
        assert area.ui == current_ui
        # Updates properties
        update_ui = AreaUiUpdate(y=12, color_rgb=[5, 6, 7])
        new_ui = area.update_ui(update_ui)
        expected_ui = AreaUi(y=12, color_rgb=[5, 6, 7], x=56)
        assert new_ui == expected_ui
        assert area.ui == expected_ui
        # Asserts the ini file is properly modified
        study_path = Path(local_study_w_areas.path)
        ui_ini = IniReader().read(study_path / "input" / "areas" / area.id / "ui.ini")
        assert ui_ini == {
            "ui": {"x": 56, "y": 12, "color_r": 5, "color_g": 6, "color_b": 7},
            "layerX": {"0": 56},
            "layerY": {"0": 12},
            "layerColor": {"0": "5,6,7"},
        }

    def test_create_area_creates_default_files(self, local_study_w_areas: Study) -> None:
        study_path = Path(local_study_w_areas.path)
        for area in local_study_w_areas.get_areas():
            assert (study_path / "input" / "st-storage" / "clusters" / area / "list.ini").exists()
            assert (study_path / "input" / "renewables" / "clusters" / area / "list.ini").exists()

    def test_create_area_with_weird_name_succeeds(self, local_study_w_areas: Study) -> None:
        local_study_w_areas.create_area("AREA_MAJ???")
        area_id = "area_maj"
        study_path = Path(local_study_w_areas.path)
        assert (study_path / TimeSeriesFileType.SOLAR.value.format(area_id=area_id)).exists()
        assert (study_path / TimeSeriesFileType.WIND.value.format(area_id=area_id)).exists()
        assert (study_path / TimeSeriesFileType.LOAD.value.format(area_id=area_id)).exists()


@pytest.mark.skipif(RUN_ON_WINDOWS, reason="This test runs randomly on Windows")
def test_remove_area(local_study_w_areas: Study) -> None:
    study = local_study_w_areas
    study_path = Path(study.path)
    hash_before_update = dirhash(study_path, "md5", excluded_files=["sets.ini"])

    # Create an area with:
    # 1 thermal cluster,
    # 1 renewable cluster
    # 1 short-term storage
    # 1 link from it to another area
    # 1 link from another area to it
    area = study.create_area("greece")
    area.create_thermal_cluster("th1")
    area.create_renewable_cluster("renewable1")
    area.create_st_storage("sts")
    study.create_link(area_from="greece", area_to="it")
    study.create_link(area_from="fr", area_to="greece")

    # Add a binding constraint referencing the link to ensure the area deletion is impossible
    term = ConstraintTerm(data=LinkData(area1="greece", area2="it"))
    bc = study.create_binding_constraint(name="bc", terms=[term])

    with pytest.raises(ReferencedObjectDeletionNotAllowed, match="Area 'greece' is not allowed to be deleted"):
        study.delete_area(area)

    # Remove the constraint and remove the area
    study.delete_binding_constraints([bc])
    study.delete_area(area)

    # The hash should be the same as before creating the area
    hash_after_update = dirhash(study_path, "md5", excluded_files=["sets.ini"])
    assert hash_before_update == hash_after_update
