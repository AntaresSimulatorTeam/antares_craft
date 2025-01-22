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
from pathlib import Path

from antares.craft.model.hydro import Hydro
from antares.craft.tools.ini_tool import IniFile, InitializationFilesTypes


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
        hydro_ini = local_study_w_areas.service.config.study_path / InitializationFilesTypes.HYDRO_INI.value
        assert hydro_ini.is_file()

    def test_create_capacity_files_for_hydro(self, local_study_w_areas):
        """
        Test that calling create_hydro on all areas triggers the creation of capacity files.
        """
        study_path = Path(local_study_w_areas.path)
        areas = local_study_w_areas.get_areas()

        for area_id, area in areas.items():
            area.create_hydro()

        for area_id in areas.keys():
            expected_paths = [
                study_path / f"input/hydro/common/capacity/creditmodulations_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/reservoir_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/waterValues_{area_id}.txt",
                study_path / f"input/hydro/common/capacity/InflowPattern_{area_id}.txt",
                study_path / f"input/hydro/series/{area_id}/ror.txt",
                study_path / f"input/hydro/series/{area_id}/mod.txt",
                study_path / f"input/hydro/series/{area_id}/mingen.txt",
                study_path / f"input/hydro/common/capacity/maxpower_{area_id}.txt",
            ]

            for expected_path in expected_paths:
                assert expected_path.is_file(), f"File not created: {expected_path}"

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
        actual_hydro_ini = IniFile(local_study_w_areas.service.config.study_path, InitializationFilesTypes.HYDRO_INI)

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
